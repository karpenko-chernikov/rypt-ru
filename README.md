# RYPT

Сайт Российского турнира юных физиков (Django + Wagtail).

## Живой сайт

| | URL |
|--|-----|
| Сайт (черновик для коллег) | https://rypt.folomin.com |
| Кабинет редакторов | https://rypt.folomin.com/dlya-redaktorov/vhod/ |

Боевой `rypt.ru` — после согласия Ивана. Этот репозиторий — **код**; контент и пользователи живут на сервере, не в Git. Админка Wagtail (`/redaktura/`) на сайте **недоступна** — всё редактирование через кабинет.

## Стек

- Python 3.12, Django 5.2, Wagtail 6.4
- SQLite (достаточно для текущего объёма)
- Статика: `rypt/static/` → `collectstatic` в `/static/`
- Кабинет редакторов: приложение `editor` (`/dlya-redaktorov/`)
- Публичные страницы: приложение `home`

## Локальная разработка

Если нужно крутить код у себя на машине (после `runserver` Django слушает localhost):

```bash
git clone https://github.com/karpenko-chernikov/rypt-ru.git
cd rypt-ru
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # при необходимости
python manage.py migrate
python manage.py seed_site
python manage.py create_editor_invite --base-url http://127.0.0.1:8000
python manage.py runserver
```

Тогда локально: http://127.0.0.1:8000 и http://127.0.0.1:8000/dlya-redaktorov/vhod/  
Это **не** продакшен и не staging — только копия на вашем компьютере.

Первый локальный редактор — по ссылке из `create_editor_invite`. Либо:

```bash
python manage.py createsuperuser
```

## Структура проекта

| Путь | Назначение |
|------|------------|
| `home/` | Модели страниц (сезоны, новости, карта России), шаблоны, команды заполнения |
| `editor/` | Кабинет: сезоны, журнал, приглашения, регионы России |
| `rypt/` | Настройки Django, URL, статика (CSS/JS/карта) |
| `deploy/` | systemd, nginx, скрипты выкладки на VPS |
| `home/management/commands/fill_season_YYYY.py` | Заполнение сезона из архивных данных |
| `home/management/commands/fill_russia_regions.py` | Реальные региональные турниры на карте |

## Кабинет редактора

- URL: `/dlya-redaktorov/` (в меню сайта **нет** ссылки)
- Вход: `/dlya-redaktorov/vhod/`
- Новые редакторы — только по **одноразовому** приглашению:

```bash
python manage.py create_editor_invite --note "Имя" --days 7
```

Группа `Editors` даёт доступ в кабинет **без** `is_staff`.  
На живом сайте `/redaktura/` и `/django-admin/` **нет** (не монтируются в production).

### Что править в кабинете

- сезоны (текущий / прошедшие), мета, задачи, сканы, результаты, IYPT, фото, материалы
- карта «Турниры в России» (`/dlya-redaktorov/rossiya/`)
- журнал правок, приглашения коллег

## Публичные разделы

Меню: Новости, Сезоны, Правила, Турниры в России, Полезные материалы, Партнёры, Контакты.

**Турниры в России** — SVG-карта субъектов (`rypt/static/maps/`), клик фиксирует карточку региона, наведение подсвечивает.

## Заполнение контента сезонов

После `seed_site` / `import_seasons` можно прогнать нужный год:

```bash
python manage.py fill_season_2008
python manage.py fill_season_2025
# …
python manage.py fill_russia_regions
```

Команды идемпотентны по смыслу сезона: перезаписывают таблицы/поля этого года.

## Деплой (staging)

Сервер: код в `/var/www/rypt`, env в `/etc/rypt.env` (не в git), сервис `rypt.service`, nginx из `deploy/nginx-rypt.conf`.

```bash
# на сервере, после rsync/git pull:
cd /var/www/rypt
source /etc/rypt.env
export DJANGO_SETTINGS_MODULE=rypt.settings.production
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
systemctl restart rypt
```

Переменные окружения — см. `.env.example`. Секреты (`DJANGO_SECRET_KEY`, пароли) **никогда** не коммитить.

Чтобы открыть Wagtail-админку `/redaktura/` на staging (вне `DEBUG`), добавьте
в `/etc/rypt.env` строку `ENABLE_WAGTAIL_ADMIN=1` и перезапустите сервис:
`systemctl restart rypt`. Django-админка `/django-admin/` остаётся недоступной.
На боевом сайте этот флаг не ставится.

## Полезные материалы

Раздел `materials` — дерево страниц Wagtail: `MaterialsIndexPage` (индекс) → `MaterialGroupPage` (группа-заголовок) → `MaterialPage` (материал). Карточки на индексе ведут на страницы материалов. Правится локально через админку Wagtail `/redaktura/` (доступна только при `DEBUG=True`); на живом сайте этого раздела в кабинете нет.

## Лицензии сторонних ассетов

- Карта России: `rypt/static/maps/` — MIT (ArmGono/ru-svg-map)

## Зеркало Telegram-канала

Сервер сайта находится в России, где Telegram заблокирован. Поэтому чтение
канала вынесено в отдельный лёгкий сервис `reader/` (FastAPI + Telethon,
Docker), который работает на зарубежном сервере и отдаёт посты через защищённый
HTTP API с bearer-токеном. Сайт тянет оттуда командой:

```bash
python manage.py sync_telegram
```

Команда сравнивает посты с уже созданными `NewsPage` (по `telegram_message_id`),
создаёт недостающие, скачивает фото/видео в медиа и публикует. Запускать её по
расписанию (cron / systemd timer) каждые 5–10 минут.

Переменные окружения на стороне сайта: `TG_READER_URL`, `TG_READER_TOKEN`,
`TG_CHANNEL` (см. `.env.example`). Подробности reader-сервиса и его переменных —
в [`reader/README.md`](reader/README.md).
