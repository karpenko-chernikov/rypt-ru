# Umami (self-hosted)

Собственная аналитика для сайта RYPT: Umami + PostgreSQL в Docker.
Работает как на том же VPS, что и сайт, так и на отдельном (зарубежном) сервере —
для кода RYPT разницы нет, меняется только `UMAMI_SCRIPT_URL`.

## Состав

- `docker-compose.yml` — Umami (`ghcr.io/umami-software/umami:postgresql-latest`) + PostgreSQL 16.
  Umami слушает только `127.0.0.1:3000` и проксируется через nginx.
- `.env.example` — секреты (`POSTGRES_PASSWORD`, `APP_SECRET`, `HASH_SALT`).
- `nginx-umami.conf` — HTTPS reverse-proxy для домена аналитики.

## Требования

- Docker + плагин `docker compose`
- nginx
- certbot (для Let's Encrypt)
- домен, A/AAAA-запись которого указывает на сервер Umami

## Установка

```bash
cd umami
cp .env.example .env
# сгенерировать секреты:
openssl rand -hex 32   # для POSTGRES_PASSWORD
openssl rand -hex 32   # для APP_SECRET
openssl rand -hex 32   # для HASH_SALT
# вписать их в .env
docker compose up -d
```

Проверка: `curl -I http://127.0.0.1:3000` — должен вернуться HTTP-ответ от Umami.

## nginx + HTTPS

Замените `analytics.example.com` в `nginx-umami.conf` на реальный домен.

### На том же сервере, где сайт RYPT

```bash
cp nginx-umami.conf /etc/nginx/sites-available/umami
# поправить server_name в файле под реальный домен
ln -sfn /etc/nginx/sites-available/umami /etc/nginx/sites-enabled/umami
nginx -t
systemctl reload nginx
certbot --nginx -d analytics.example.com --non-interactive --agree-tos --register-unsafely-without-email --redirect
```

Если на сервере уже есть `deploy/nginx-rypt.conf`, новый server-блок просто добавляется
к конфигурации nginx — оба сайта работают параллельно.

### На отдельном (зарубежном) сервере

Скопировать каталог `umami/` на сервер (или развернуть из git) и выполнить те же
команды: установить docker + nginx + certbot, `docker compose up -d`, затем nginx + certbot.

## Работа без домена

Отдельный домен не обязателен. Но скрипт трекинга должен отдаваться по HTTPS:
на боевом `https://rypt.folomin.com` браузер заблокирует HTTP-скрипт как mixed content.

### Доступ в админку Umami

Umami уже слушает `127.0.0.1:3000`. Админку можно открыть через SSH-туннель:

```bash
ssh -L 3000:127.0.0.1:3000 user@server
# затем в браузере: http://localhost:3000
```

### Публичный URL для скрипта

Выберите один из вариантов:

1. **HTTPS-туннель (быстрее всего).** Cloudflare Tunnel или ngrok, проброшенные
   на `127.0.0.1:3000`, дают `https://...` без своего домена. Тогда:
   `UMAMI_SCRIPT_URL=https://<tunnel-host>/script.js`.
2. **Публичный IP + sslip.io/nip.io.** Если у сервера белый IP, используйте
   `https://<IP>.sslip.io` (или `https://<IP>.nip.io`), выпустите сертификат
   certbot на этот домен и проксируйте через nginx, как в разделе выше.
3. **Только локальная проверка без HTTPS.** Можно открыть
   `http://<server-ip>:3000`, если в `docker-compose.yml` заменить
   `127.0.0.1:3000:3000` на `3000:3000`. На боевом сайте такой `UMAMI_SCRIPT_URL`
   не заработает из-за mixed content.

## Первый вход и создание сайта

1. Открыть `https://analytics.example.com`.
2. Войти по умолчанию: логин `admin`, пароль `umami`.
3. Сразу сменить пароль: **Settings → Profile**.
4. **Settings → Websites → Add website**: ввести имя (например `RYPT`) и домен
   `rypt.folomin.com`. Можно не указывать домен — тогда трекинг работает с любого
   сайта, где подключён скрипт.
5. Скопировать **Website ID** (UUID) созданного сайта.

## Подключение к сайту RYPT

На сервере RYPT в `/etc/rypt.env` добавить:

```
UMAMI_SCRIPT_URL=https://analytics.example.com/script.js
UMAMI_WEBSITE_ID=<скопированный Website ID>
# UMAMI_DOMAINS=rypt.folomin.com
```

Затем:

```bash
systemctl restart rypt
```

Трекинг подключается только на публичных страницах (`rypt/templates/base.html`);
кабинет редактора (`/dlya-redaktorov/`) не трекается. Пустые значения переменных
выключают трекинг.

## Резервное копирование и обновление

- Данные — в Docker-томе `umami_umami-db`:
  `docker compose exec db pg_dump -U umami umami > backup.sql`.
- Обновление Umami:
  `docker compose pull umami && docker compose up -d`.
- `docker compose` используется из каталога `umami/`.
