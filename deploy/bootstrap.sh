#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

APP=/var/www/rypt
apt-get update -qq
apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx

mkdir -p "$APP" /var/www/rypt/media
chown -R www-data:www-data "$APP"

if [[ ! -f /etc/rypt.env ]]; then
  key=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
  cat >/etc/rypt.env <<EOF
DJANGO_SECRET_KEY=${key}
ALLOWED_HOSTS=rypt.folomin.com
WAGTAILADMIN_BASE_URL=https://rypt.folomin.com
EOF
  chmod 640 /etc/rypt.env
  chown root:www-data /etc/rypt.env
fi

cd "$APP"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -U pip
.venv/bin/pip install -q -r requirements.txt

set -a
# shellcheck disable=SC1091
source /etc/rypt.env
set +a
export DJANGO_SETTINGS_MODULE=rypt.settings.production

.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py seed_site
.venv/bin/python manage.py import_seasons
.venv/bin/python manage.py collectstatic --noinput
chown -R www-data:www-data "$APP"
chown root:www-data /etc/rypt.env
chmod 640 /etc/rypt.env

if [[ ! -f /root/rypt-editor-password.txt ]]; then
  pass=$(python3 -c "import secrets; print(secrets.token_urlsafe(12))")
  DJANGO_SETTINGS_MODULE=rypt.settings.production .venv/bin/python - <<PY
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rypt.settings.production")
from django.contrib.auth import get_user_model
User = get_user_model()
password = "${pass}"
u, created = User.objects.get_or_create(
    username="redaktor",
    defaults={"email": "redaktor@rypt.folomin.com", "is_staff": True, "is_superuser": True},
)
u.set_password(password)
u.is_staff = True
u.is_superuser = True
u.save()
print("editor user ready")
PY
  printf '%s\n' "$pass" >/root/rypt-editor-password.txt
  chmod 600 /root/rypt-editor-password.txt
fi

cp "$APP/deploy/rypt.service" /etc/systemd/system/rypt.service
cp "$APP/deploy/nginx-rypt.conf" /etc/nginx/sites-available/rypt
ln -sfn /etc/nginx/sites-available/rypt /etc/nginx/sites-enabled/rypt
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl daemon-reload
systemctl enable --now rypt
systemctl restart rypt
systemctl reload nginx

# Let's Encrypt: may fail while Cloudflare proxy is on; site can still work via Cloudflare HTTPS.
certbot --nginx -d rypt.folomin.com --non-interactive --agree-tos --register-unsafely-without-email --redirect || true

systemctl is-active rypt nginx
echo "BOOTSTRAP_DONE"
