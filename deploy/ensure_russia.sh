#!/bin/bash
# Обновить страницу «Турниры в России» реальными данными (без wipe новостей).
set -euo pipefail
cd /var/www/rypt
export DJANGO_SETTINGS_MODULE=rypt.settings.production
set -a
# shellcheck disable=SC1091
source /etc/rypt.env
set +a

.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py fill_russia_regions
.venv/bin/python manage.py collectstatic --noinput
chown -R www-data:www-data /var/www/rypt
systemctl restart rypt
systemctl is-active rypt
echo DEPLOY_OK
