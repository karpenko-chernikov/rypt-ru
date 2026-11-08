#!/bin/bash
# Обновить страницу «Турниры в России» реальными данными (без wipe новостей).
set -euo pipefail
REL=/srv/rypt/current

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

run_runtime "$REL/.venv/bin/python" "$REL/manage.py" migrate --noinput
run_runtime "$REL/.venv/bin/python" "$REL/manage.py" fill_russia_regions
run_deploy_static "$REL/static" \
  "$REL/.venv/bin/python" "$REL/manage.py" collectstatic --noinput

systemctl restart rypt
systemctl is-active rypt
echo DEPLOY_OK
