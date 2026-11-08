#!/bin/bash
# Откат на предыдущий release: меняет местами current и previous и перезапускает
# сервис. SQLite-миграции при этом не откатываются автоматически (forward-only);
# при необходимости откатывайте БД отдельно.
set -euo pipefail

CURRENT=/srv/rypt/current
PREVIOUS=/srv/rypt/previous

if [[ ! -L "$PREVIOUS" || ! -d "$(readlink -f "$PREVIOUS")" ]]; then
  echo "No previous release available" >&2
  exit 1
fi

old="$(readlink -f "$CURRENT")"
ln -sfn "$(readlink -f "$PREVIOUS")" "$CURRENT"
ln -sfn "$old" "$PREVIOUS"

systemctl restart rypt
systemctl restart nginx
systemctl is-active rypt nginx
echo "ROLLED_BACK_TO=$(readlink -f "$CURRENT")"
