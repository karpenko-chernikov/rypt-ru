#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------------------
# Выкладка RYPT.
#
# Закрывает аудит «runtime может подменить код при выкладке»:
#   * код и venv живут в release-дереве, которым владеет rypt-deploy,
#     а runtime-пользователь rypt получает только чтение/исполнение (r-x);
#   * pip и collectstatic исполняются от rypt-deploy, миграции — от rypt;
#   * systemd unit и конфиг Nginx ставятся из проверенного release-дерева;
#   * SQLite, media и временные файлы вынесены в /var/lib/rypt.
#
# Запуск:  sudo deploy/bootstrap.sh [SRC]
#   SRC — checkout исходников (по умолчанию /srv/rypt/source), владелец rypt-deploy.
# ---------------------------------------------------------------------------

SRC="${1:-/srv/rypt/source}"
RELEASE_ROOT=/srv/rypt
REL="$RELEASE_ROOT/releases/$(date +%Y%m%d-%H%M%S)"
OLD_APP=/var/www/rypt

apt-get update -qq
apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx rsync

# --- пользователи -----------------------------------------------------------
getent group rypt >/dev/null || groupadd --system rypt
getent passwd rypt >/dev/null || useradd --system --gid rypt --no-create-home \
  --home-dir /var/lib/rypt --shell /usr/sbin/nologin rypt
getent passwd rypt-deploy >/dev/null || useradd --system --gid rypt --no-create-home \
  --home-dir /var/lib/rypt-deploy --shell /usr/sbin/nologin rypt-deploy

# Nginx читает статику внутри release-дерева через /srv/rypt/current/static.
id -nG www-data | grep -qw rypt || usermod -aG rypt www-data

# --- каталоги ---------------------------------------------------------------
install -d -o root        -g rypt      -m 0750 "$RELEASE_ROOT" "$RELEASE_ROOT/releases"
install -d -o rypt-deploy -g rypt      -m 0750 "$RELEASE_ROOT/source" "$RELEASE_ROOT/data"
install -d -o rypt-deploy -g rypt -m 0750 /var/lib/rypt-deploy
install -d -o rypt        -g rypt      -m 0750 /var/lib/rypt/db /var/lib/rypt/tmp /var/lib/rypt/pycache
install -d -o rypt        -g www-data  -m 0750 /var/lib/rypt/media

# Исторические сканы (читаются fill-командами) переносим до сборки релиза,
# чтобы в новом релизе сразу появился symlink на них.
if [[ -d "$OLD_APP/_scan_preview" && ! -e "$RELEASE_ROOT/data/_scan_preview" ]]; then
  echo "==> migrating _scan_preview from $OLD_APP"
  mv "$OLD_APP/_scan_preview" "$RELEASE_ROOT/data/_scan_preview" 2>/dev/null || true
fi
chown -R rypt-deploy:rypt "$RELEASE_ROOT/data"

# --- env --------------------------------------------------------------------
# Production fail-closed: DJANGO_SECRET_KEY, ALLOWED_HOSTS и
# WAGTAILADMIN_BASE_URL обязательны; недостающие дополняем ниже.
if [[ ! -f /etc/rypt.env ]]; then
  key=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
  cat >/etc/rypt.env <<EOF
DJANGO_SECRET_KEY=${key}
ALLOWED_HOSTS=rosypt.ru
WAGTAILADMIN_BASE_URL=https://rosypt.ru
EOF
fi
# Дописываем недостающие переменные (нужно при первом переезде и защищает
# от случайного удаления строки в /etc/rypt.env).
{
  grep -q '^DJANGO_SECRET_KEY=' /etc/rypt.env || echo "DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
  grep -q '^ALLOWED_HOSTS=' /etc/rypt.env || echo 'ALLOWED_HOSTS=rosypt.ru'
  grep -q '^WAGTAILADMIN_BASE_URL=' /etc/rypt.env || echo 'WAGTAILADMIN_BASE_URL=https://rosypt.ru'
  grep -q '^DATABASE_PATH=' /etc/rypt.env || echo 'DATABASE_PATH=/var/lib/rypt/db/db.sqlite3'
  grep -q '^MEDIA_ROOT='    /etc/rypt.env || echo 'MEDIA_ROOT=/var/lib/rypt/media'
  grep -q '^STATIC_ROOT='   /etc/rypt.env || echo 'STATIC_ROOT=/srv/rypt/current/static'
} >>/etc/rypt.env
chmod 640 /etc/rypt.env
chown root:rypt /etc/rypt.env

set -a
# shellcheck disable=SC1091
source /etc/rypt.env
set +a
export DJANGO_SETTINGS_MODULE=rypt.settings.production

run_deploy() {
  setpriv --reuid=rypt-deploy --regid=rypt --init-groups -- bash -c '
    set -a; . /etc/rypt.env; set +a
    export DJANGO_SETTINGS_MODULE=rypt.settings.production
    export HOME=/var/lib/rypt-deploy
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    exec "$@"
  ' _ "$@"
}
run_deploy_static() {
  local static_root="$1"; shift
  setpriv --reuid=rypt-deploy --regid=rypt --init-groups -- bash -c '
    set -a; . /etc/rypt.env; set +a
    export DJANGO_SETTINGS_MODULE=rypt.settings.production
    export HOME=/var/lib/rypt-deploy
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    export STATIC_ROOT="$1"
    shift
    exec "$@"
  ' _ "$static_root" "$@"
}
run_runtime() {
  setpriv --reuid=rypt --regid=rypt --init-groups -- bash -c '
    set -a; . /etc/rypt.env; set +a
    export DJANGO_SETTINGS_MODULE=rypt.settings.production
    export HOME=/var/lib/rypt
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONPYCACHEPREFIX=/var/lib/rypt/pycache
    export TMPDIR=/var/lib/rypt/tmp
    exec "$@"
  ' _ "$@"
}

[[ -f "$SRC/manage.py" ]] || { echo "Source checkout not found: $SRC/manage.py" >&2; exit 1; }

# --- сборка релиза (runtime-сервис в это время ещё работает) ----------------
echo "==> building release $REL from $SRC"
install -d -o rypt-deploy -g rypt -m 0750 "$REL"
rsync -a --delete --exclude-from="$SRC/deploy/rsync-exclude.txt" "$SRC/" "$REL/"
chown -hR rypt-deploy:rypt "$REL"
chmod -R u=rwX,g=rX,o= "$REL"

# Исторические fill-команды читают _scan_preview в корне release-дерева.
if [[ -e "$RELEASE_ROOT/data/_scan_preview" ]]; then
  ln -sfn "$RELEASE_ROOT/data/_scan_preview" "$REL/_scan_preview"
fi

run_deploy /usr/bin/python3 -m venv "$REL/.venv"
run_deploy "$REL/.venv/bin/pip" install -q -U pip
run_deploy "$REL/.venv/bin/pip" install -q -r "$REL/requirements.txt"
run_deploy_static "$REL/static" \
  "$REL/.venv/bin/python" "$REL/manage.py" collectstatic --noinput
chown -hR rypt-deploy:rypt "$REL/.venv" "$REL/static"

# --- остановка и однократный переезд данных ---------------------------------
echo "==> stopping runtime for data migration"
systemctl stop rypt 2>/dev/null || true

if [[ -d "$OLD_APP" ]]; then
  if [[ -f "$OLD_APP/db.sqlite3" && ! -e /var/lib/rypt/db/db.sqlite3 ]]; then
    echo "==> migrating database from $OLD_APP"
    mv "$OLD_APP"/db.sqlite3* /var/lib/rypt/db/ 2>/dev/null || true
  fi
  if [[ -d "$OLD_APP/media" && -z "$(ls -A /var/lib/rypt/media 2>/dev/null)" ]]; then
    echo "==> migrating media from $OLD_APP"
    find "$OLD_APP/media" -mindepth 1 -maxdepth 1 -exec mv -t /var/lib/rypt/media {} + 2>/dev/null || true
  fi
fi
chown -R rypt:rypt /var/lib/rypt/db /var/lib/rypt/tmp /var/lib/rypt/pycache
chown -R rypt:www-data /var/lib/rypt/media

# --- миграции — с минимальными правами (runtime) -----------------------------
# seed_site / import_seasons здесь не запускаются: они деструктивны
# (удаляют новости и пересоздают задания) и нужны только при первичной
# установке на пустую БД.
echo "==> applying migrations (runtime user)"
run_runtime "$REL/.venv/bin/python" "$REL/manage.py" migrate --noinput

# Аккаунты редакторов создаются только через одноразовые приглашения
# (manage.py create_editor_invite / интерфейс приглашений). Автосоздание
# общего superuser удалено.

# --- атомарное переключение и установка unit/nginx из проверенного релиза ---
echo "==> switching release"
if [[ -L "$RELEASE_ROOT/current" ]]; then
  ln -sfn "$(readlink -f "$RELEASE_ROOT/current")" "$RELEASE_ROOT/previous"
fi
ln -sfn "$REL" "$RELEASE_ROOT/current"

install -o root -g root -m 0644 "$REL/deploy/rypt.service" /etc/systemd/system/rypt.service
install -o root -g root -m 0644 "$REL/deploy/nginx-rypt.conf" /etc/nginx/sites-available/rypt
ln -sfn /etc/nginx/sites-available/rypt /etc/nginx/sites-enabled/rypt
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl daemon-reload
systemctl enable --now rypt
systemctl restart rypt
# restart (а не reload): чтобы nginx-воркеры увидели новую группу rypt у www-data
systemctl restart nginx

# Let's Encrypt: может упасть, пока включён прокси Cloudflare; сайт всё равно
# работает через HTTPS Cloudflare.
certbot --nginx -d rosypt.ru --non-interactive --agree-tos \
  --register-unsafely-without-email --redirect || true

# certbot --nginx может переписать server-блоки и вернуть редирект/заголовки
# к $host. Проверяем канонические директивы из deploy/nginx-rypt.conf и, если
# certbot их затёр, переустанавливаем конфиг из release-дерева.
if ! grep -q "proxy_set_header Host rosypt.ru" /etc/nginx/sites-enabled/rypt \
   || ! grep -q "proxy_set_header X-Forwarded-Host rosypt.ru" /etc/nginx/sites-enabled/rypt \
   || ! grep -q "return 444" /etc/nginx/sites-enabled/rypt; then
  install -o root -g root -m 0644 "$REL/deploy/nginx-rypt.conf" /etc/nginx/sites-available/rypt
  nginx -t
  systemctl reload nginx
fi

# admin.rosypt.ru -> Wagtail /redaktura/ (redirect). Получаем сертификат до
# включения server-блока: иначе nginx -t упадёт на отсутствующих файлах
# /etc/letsencrypt/live/admin.rosypt.ru/. Webroot-челлендж обслуживается
# дефолтным блоком порта 80 (root /var/www/html).
certbot certonly --webroot -w /var/www/html -d admin.rosypt.ru \
  --non-interactive --agree-tos --register-unsafely-without-email || true
if [[ -f /etc/letsencrypt/live/admin.rosypt.ru/fullchain.pem ]]; then
  install -o root -g root -m 0644 "$REL/deploy/nginx-admin.conf" /etc/nginx/sites-available/admin
  ln -sfn /etc/nginx/sites-available/admin /etc/nginx/sites-enabled/admin
  nginx -t
  systemctl reload nginx
fi

# Старый путь больше не используется — делаем его inert (владелец root).
if [[ -d "$OLD_APP" ]]; then
  chown -R root:root "$OLD_APP"
fi

systemctl is-active rypt nginx
echo "BOOTSTRAP_DONE release=$(readlink -f "$RELEASE_ROOT/current")"
