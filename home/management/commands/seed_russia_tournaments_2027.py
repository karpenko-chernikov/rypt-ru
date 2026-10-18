"""Заполнить / обновить региональные турниры сезона 2026–2027."""

from datetime import date

from django.core.management.base import BaseCommand

from editor.services import publish_page
from home.models import (
    RegionalTournament,
    RegionalTournamentProblem,
    RussiaTournamentsPage,
    TournamentProblem,
    current_tournament_season,
)

# Задачи: либо "all", либо список названий (как в TournamentProblem.title).
TOURNAMENTS = [
    {
        "slug": "voronezh",
        "region_code": "RU-VOR",
        "title": "Воронежский турнир юных физиков",
        "city": "Воронеж",
        "date_start": date(2026, 11, 5),
        "date_end": date(2026, 11, 6),
        "date_note": "5–6 ноября",
        "contacts": (
            "Елена Ивановна Деревягина\n"
            "+7 (951) 548-65-46, kontakt08@mail.ru\n"
            "VK: https://vk.ru/voronezhskiy_turnir"
        ),
        "info": (
            "<p>Воронежский турнир юных физиков. "
            '<a href="https://vk.ru/voronezhskiy_turnir">Группа VK</a>.</p>'
        ),
        "results_url": "https://vk.ru/voronezhskiy_turnir",
        "results_label": "Группа VK",
        "problems": [
            "Дисковый спектрометр",
            "Тише едешь",
            "Игрек-маятник",
            "Тонущая воронка",
            "Захлопывающаяся книга",
            "Вихревая нить",
            "Магнитная карусель",
            "Меловое стаккато",
            "Охлаждение напитка",
            "Вихревой маятник",
        ],
    },
    {
        "slug": "tula",
        "region_code": "RU-TUL",
        "title": "Тульский турнир юных физиков",
        "city": "Новомосковск, ЦПОД «Созвездие»",
        "date_start": date(2026, 11, 18),
        "date_end": date(2026, 11, 19),
        "date_note": "18–19 ноября (смена 16–22 ноября)",
        "contacts": (
            "Ирина Викторовна Рыжонкова\n"
            "sozvezdie@tularegion.org\n"
            "Зинкевич Александр Алексеевич\n"
            "+79138992759\n"
            "ЦПОД ТО «Созвездие», г. Новомосковск"
        ),
        "info": (
            "<p>Тульский турнир юных физиков проходит в рамках большой физической смены "
            "центра «Сириус — Созвездие» (Новомосковск): смена <strong>16–22 ноября</strong>, "
            "сам турнир — <strong>18–19 ноября</strong>.</p>"
            "<p>К турниру готовятся уже сейчас 6 команд (30 школьников и 8 научных руководителей).</p>"
            "<p>Организатор: ЦПОД ТО «Созвездие», г. Новомосковск.</p>"
        ),
        "problems": None,
    },
    {
        "slug": "mos-mipt",
        "region_code": "RU-MOS",
        "title": "Московский турнир юных физиков",
        "city": "МФТИ, Долгопрудный",
        "date_start": date(2026, 11, 28),
        "date_end": date(2026, 11, 30),
        "date_note": "28–30 ноября",
        "contacts": (
            "Елена Сергеевна Зворыгина\n"
            "+79199610805, zvorygina@phystech.edu\n"
            "Организация: mos.phys.tournament@yandex.com\n"
            "Сайт: https://mos.iypt.ru/\n"
            "VK: https://vk.com/mosypt"
        ),
        "info": (
            "<p>Очный этап Московского турнира юных физиков — "
            "28–30 ноября в МФТИ. "
            '<a href="https://mos.iypt.ru/">mos.iypt.ru</a>.</p>'
        ),
        "results_url": "https://mos.iypt.ru/",
        "results_label": "Сайт турнира",
        "problems": [
            "Придумай сам: Очки-обскуры",
            "Дисковый спектрометр",
            "Тише едешь",
            "Смотрим на звук",
            "Тонущая воронка",
            "Вихревая нить",
            "Вихревой маятник",
            "Охлаждение напитка",
            "Захлопывающаяся книга",
        ],
    },
    {
        "slug": "kaliningrad",
        "region_code": "RU-KGD",
        "title": "Калининградский турнир юных физиков",
        "city": "33 школа",
        "date_start": date(2026, 12, 18),
        "date_end": date(2026, 12, 20),
        "date_note": "18–20 декабря",
        "contacts": "",
        "info": (
            "<p>Калининградский турнир юных физиков, сезон 2026–2027. "
            "Формат: 3 отборочных боя, 3 бесплатных отказа, третий бой — задача по выбору без вызова. "
            '<a href="/static/docs/KalTYuF_2026-2027_Broshyura.pdf">Брошюра турнира (PDF)</a>.</p>'
        ),
        "results_url": "/static/docs/KalTYuF_2026-2027_Broshyura.pdf",
        "results_label": "Брошюра сезона 2026–2027",
        "problems": [
            "Тише едешь",
            "Игрек-маятник",
            "Тонущая воронка",
            "Фотографическое боке",
            "Звукоизоляция",
            "Меловое стаккато",
            "Неньютоновские червячки",
            "Охлаждение напитка",
            "Магнитная карусель",
        ],
    },
    {
        "slug": "beaver",
        "region_code": "ONLINE",
        "title": "Кубок Бобра",
        "city": "онлайн",
        "date_start": date(2026, 12, 24),
        "date_end": date(2026, 12, 27),
        "date_note": "24–27 декабря",
        "contacts": "Telegram: https://t.me/+qqS7D9uvuFFhMDUy",
        "info": (
            "<p>Кубок Бобра — онлайн-турнир. Играются все 17 задач сезона. "
            '<a href="https://t.me/+qqS7D9uvuFFhMDUy">Telegram</a>.</p>'
        ),
        "results_url": "https://t.me/+qqS7D9uvuFFhMDUy",
        "results_label": "Telegram",
        "problems": "all",
    },
    {
        "slug": "zonal-spb",
        "region_code": "RU-SPE",
        "title": "Зональный турнир юных физиков",
        "city": "СПбГУ",
        "date_start": None,
        "date_end": None,
        "date_note": "декабрь 2026 (ориентировочно)",
        "contacts": (
            "Сергей Сергеевич Пивоваров\n"
            "25shadow@mail.ru"
        ),
        "info": (
            "<p>Проводится на площадке СПбГУ, обычно в декабре. "
            "Приглашаются команды Санкт-Петербурга, Ленинградской области, "
            "Северо-Запада и других регионов.</p>"
        ),
        "results_url": "",
        "results_label": "",
        "problems": None,
    },
    {
        "slug": "leningrad",
        "region_code": "RU-LEN",
        "title": "Турнир юных физиков Ленинградской области",
        "city": "центр «Интеллект»",
        "date_start": None,
        "date_end": None,
        "date_note": "",
        "contacts": (
            "Светлана Валерьевна Фролова\n"
            "+7 (812) 434-94-29, konfint@yandex.ru\n"
            "Сайт: https://center-intellect.ru/konferentsii-tsentra/physics_tournament/"
        ),
        "info": (
            "<p>Региональный этап в Ленинградской области, центр «Интеллект». "
            '<a href="https://center-intellect.ru/konkursnye-meropriyatiya/konferentsii-forumy-turniry/regionalnyy-etap-vserossiyskogo-turnira-yunykh-fizikov-v-leningradskoy-oblasti/">'
            "Страница мероприятия</a>.</p>"
        ),
        "results_url": "https://center-intellect.ru/konferentsii-tsentra/physics_tournament/",
        "results_label": "Сайт центра «Интеллект»",
        "problems": None,
    },
    {
        "slug": "ural",
        "region_code": "RU-SVE",
        "title": "Уральский турнир юных физиков",
        "city": "СУНЦ УрФУ, Екатеринбург",
        "date_start": date(2027, 1, 3),
        "date_end": date(2027, 1, 8),
        "date_note": "3–8 января 2027 (уточняется)",
        "contacts": (
            "Ольга Викторовна Инишева\n"
            "+79222070913, o.v.inisheva@urfu.ru\n"
            "VK: https://vk.com/club185132556\n"
            "Уральский физ. турнир: https://lyceum.urfu.ru/uft"
        ),
        "info": (
            "<p>Проводится на базе СУНЦ УрФУ (Екатеринбург). "
            '<a href="https://vk.com/club185132556">Группа VK</a>.</p>'
        ),
        "results_url": "https://vk.com/club185132556",
        "results_label": "Группа VK",
        "problems": None,
    },
    {
        "slug": "mosgor",
        "region_code": "RU-MOW",
        "title": "Московский городской турнир юных физиков",
        "city": "физфак МГУ",
        "date_start": date(2027, 1, 26),
        "date_end": None,
        "date_note": "после 25 января (зимние каникулы)",
        "contacts": (
            "Клим Дмитриевич Сладков\n"
            "mosypt@ya.ru\n"
            "Сайт: https://tournament.phys.msu.ru/\n"
            "Telegram: https://t.me/physics_tournament"
        ),
        "info": (
            "<p>МосГорТЮФ 2027 — на физическом факультете МГУ "
            "(Москва, Ленинские горы, д. 1, стр. 2, м. Университет) "
            "на зимних студенческих каникулах — после 25 января. "
            '<a href="https://tournament.phys.msu.ru/">tournament.phys.msu.ru</a>, '
            'задачи: <a href="https://tournament.phys.msu.ru/tasks/">tasks</a>.</p>'
        ),
        "results_url": "https://tournament.phys.msu.ru/",
        "results_label": "Сайт МосГорТЮФ",
        "problems": [
            "Придумай сам: Очки-обскуры",
            "Дисковый спектрометр",
            "Тише едешь",
            "Поющий конденсатор",
            "Игрек-маятник",
            "Смотрим на звук",
            "Тонущая воронка",
            "Звукоизоляция",
            "Охлаждение напитка",
            "Магнитная карусель",
        ],
    },
    {
        "slug": "sib",
        "region_code": "RU-NVS",
        "title": "Сибирский турнир юных физиков",
        "city": "НГУ",
        "date_start": None,
        "date_end": None,
        "date_note": "конец января",
        "contacts": (
            "Михаил Юрьевич Солодовников, президент Сибирского ТЮФ\n"
            "smu1970@mail.ru\n"
            "Юрий Леонидович Башкатов, СУНЦ НГУ\n"
            "bashkatov.yury@gmail.com\n"
            "Сайт: https://sesc.nsu.ru/research/tournament/\n"
            "VK: https://vk.ru/sibypt\n"
            "Telegram: @Mikhail_Solodovnikov\n"
            "Телефон: +7 913 767-46-27"
        ),
        "info": (
            "<p>Сибирский турнир юных физиков (СибТЮФ), НГУ (Академгородок). "
            "XVI СибТЮФ — конец января 2027. "
            '<a href="https://vk.ru/sibypt">vk.ru/sibypt</a>.</p>'
        ),
        "results_url": "https://vk.ru/sibypt",
        "results_label": "Группа СибТЮФа",
        "problems": "keep",  # не трогать уже выбранные
    },
    {
        "slug": "crimea",
        "region_code": "RU-CR",
        "title": "Крымский турнир юных физиков",
        "city": "",
        "date_start": None,
        "date_end": None,
        "date_note": "",
        "contacts": "Михаил Владимирович Анищенко\nmacl.13@mail.ru",
        "info": (
            "<p>Крымский (республиканский) этап. "
            "Задачи сезона — по официальному списку республиканского этапа.</p>"
        ),
        "results_url": "",
        "results_label": "",
        "problems": "keep",
    },
    {
        "slug": "omsk",
        "region_code": "RU-OMS",
        "title": "Омский турнир юных физиков",
        "city": "Омск",
        "date_note": "",
        "contacts": "Наталья Яганова\nn_y89@mail.ru",
        "info": "<p>Омский турнир юных физиков.</p>",
        "problems": None,
    },
    {
        "slug": "salekhard",
        "region_code": "RU-YAN",
        "title": "Турнир юных физиков Салехарда",
        "city": "Салехард",
        "date_note": "",
        "contacts": (
            "Елена Майорова\n"
            "sh_4@rambler.ru\n"
            "VK: https://vk.com/salekhardyypt"
        ),
        "info": (
            '<p>ТЮФ Салехарда. <a href="https://vk.com/salekhardyypt">Группа VK</a>.</p>'
        ),
        "results_url": "https://vk.com/salekhardyypt",
        "results_label": "Группа VK",
        "problems": None,
    },
    {
        "slug": "bryansk",
        "region_code": "RU-BRY",
        "title": "Брянский турнир юных физиков",
        "city": "Брянск",
        "date_note": "",
        "contacts": (
            "Сергей Григорьевич Малинников\n"
            "Priembgu@mail.ru"
        ),
        "info": "<p>Брянский турнир юных физиков.</p>",
        "problems": None,
    },
    {
        "slug": "buryatia",
        "region_code": "RU-BU",
        "title": "Бурятский турнир юных физиков",
        "city": "Бурятия",
        "date_note": "",
        "contacts": (
            "Валентина Ивановна Ваганова\n"
            "Valen51@mail.ru"
        ),
        "info": "<p>Бурятский турнир юных физиков.</p>",
        "problems": None,
    },
    {
        "slug": "tver",
        "region_code": "RU-TVE",
        "title": "Тверской турнир юных физиков",
        "city": "Тверь",
        "date_note": "",
        "contacts": (
            "Радий Юрьевич Скребцов\n"
            "rad88@ya.ru"
        ),
        "info": "<p>Тверской турнир юных физиков.</p>",
        "problems": None,
    },
    {
        "slug": "kirov",
        "region_code": "RU-KIR",
        "title": "Турнир юных физиков в городе Киров",
        "city": "Киров",
        "date_note": "",
        "contacts": (
            "Анна Кимовна Напольская\n"
            "anna_napolskaya@mail.ru"
        ),
        "info": "<p>Турнир юных физиков в Кирове.</p>",
        "problems": None,
    },
    {
        "slug": "penza",
        "region_code": "RU-PNZ",
        "title": "Турнир юных физиков Пензы",
        "city": "Пенза",
        "date_note": "",
        "contacts": (
            "Владислав Рябиков\n"
            "ypt.penza@mail.ru\n"
            "VK: https://vk.com/kvantoriumpenza"
        ),
        "info": (
            '<p>ТЮФ Пензы. <a href="https://vk.com/kvantoriumpenza">Группа VK</a>.</p>'
        ),
        "results_url": "https://vk.com/kvantoriumpenza",
        "results_label": "Группа VK",
        "problems": None,
    },
    {
        "slug": "irkutsk",
        "region_code": "RU-IRK",
        "title": "Иркутский турнир юных физиков",
        "city": "Иркутск",
        "date_note": "",
        "contacts": "VK: https://vk.ru/irkut_ypt",
        "info": (
            '<p>Иркутский ТЮФ. <a href="https://vk.ru/irkut_ypt">Группа VK</a>.</p>'
        ),
        "results_url": "https://vk.ru/irkut_ypt",
        "results_label": "Группа VK",
        "problems": None,
    },
    {
        "slug": "ulyanovsk",
        "region_code": "RU-ULY",
        "title": "Ульяновский турнир юных физиков",
        "city": "Ульяновск",
        "date_note": "",
        "contacts": "Telegram: https://t.me/+DU0-7Dw17iE2NzI6",
        "info": (
            '<p>Ульяновский ТЮФ. '
            '<a href="https://t.me/+DU0-7Dw17iE2NzI6">Telegram</a>.</p>'
        ),
        "results_url": "https://t.me/+DU0-7Dw17iE2NzI6",
        "results_label": "Telegram",
        "problems": None,
    },
    {
        "slug": "ftysh-mephi",
        "region_code": "RU-MOW",
        "title": "Физический турнир юных школьников",
        "city": "НИЯУ МИФИ",
        "date_start": None,
        "date_end": None,
        "date_note": "весной 2027",
        "contacts": (
            "Ольга Викторовна Инишева\n"
            "+79222070913, o.v.inisheva@urfu.ru\n"
            "VK: https://vk.ru/ros_ypt"
        ),
        "info": (
            "<p>Физический турнир юных школьников — НИЯУ МИФИ, весной 2027. "
            '<a href="https://vk.ru/ros_ypt">Группа VK</a>.</p>'
        ),
        "results_url": "https://vk.ru/ros_ypt",
        "results_label": "Группа VK",
        "problems": [
            "Придумай сам: Очки-обскуры",
            "Дисковый спектрометр",
            "Тише едешь",
            "Смотрим на звук",
            "Тонущая воронка",
            "Вихревая нить",
            "Звукоизоляция",
            "Вихревой маятник",
            "Охлаждение напитка",
            "Захлопывающаяся книга",
        ],
    },
    {
        "slug": "tatarstan",
        "region_code": "RU-TA",
        "title": "ТатТЮФ",
        "city": "Татарстан",
        "date_note": "",
        "contacts": "VK: https://vk.ru/club221140625",
        "info": (
            '<p>ТатТЮФ (Республика Татарстан). '
            '<a href="https://vk.ru/club221140625">Группа VK</a>.</p>'
        ),
        "results_url": "https://vk.ru/club221140625",
        "results_label": "Группа VK",
        "problems": None,
    },
]


class Command(BaseCommand):
    help = "Upsert regional tournaments for season 2026/27 (matrix + map)"

    def handle(self, *args, **options):
        page = RussiaTournamentsPage.objects.first()
        cur = current_tournament_season()
        if not page or not cur:
            self.stderr.write(f"Need page and current season, got {page!r} {cur!r}")
            return

        by_title = {p.title.strip(): p for p in cur.problems.all()}
        all_problems = list(cur.problems.all().order_by("number"))

        # Rename legacy slugs from region codes if needed
        for old_code, new_slug in (
            ("ru-nvs", "sib"),
            ("ru-kgd", "kaliningrad"),
            ("ru-cr", "crimea"),
        ):
            RegionalTournament.objects.filter(page=page, slug=old_code).update(slug=new_slug)

        for i, spec in enumerate(TOURNAMENTS):
            slug = spec["slug"]
            defaults = {
                "region_code": spec["region_code"],
                "has_tournament": True,
                "title": spec["title"],
                "city": spec.get("city") or "",
                "date_start": spec.get("date_start"),
                "date_end": spec.get("date_end"),
                "date_note": spec.get("date_note") or "",
                "contacts": spec.get("contacts") or "",
                "info": spec.get("info") or "",
                "results_url": spec.get("results_url") or "",
                "results_label": spec.get("results_label") or "",
                "sort_order": i,
            }
            reg, created = RegionalTournament.objects.get_or_create(
                page=page,
                slug=slug,
                defaults=defaults,
            )
            if not created:
                for k, v in defaults.items():
                    setattr(reg, k, v)
                reg.save()

            mode = spec.get("problems")
            if mode == "keep":
                pass
            elif mode == "all":
                RegionalTournamentProblem.objects.filter(
                    tournament=reg, problem__page=cur
                ).delete()
                for p in all_problems:
                    RegionalTournamentProblem.objects.create(tournament=reg, problem=p)
            elif isinstance(mode, list):
                missing = [t for t in mode if t not in by_title]
                if missing:
                    self.stderr.write(f"{slug}: missing titles {missing}")
                RegionalTournamentProblem.objects.filter(
                    tournament=reg, problem__page=cur
                ).delete()
                for title in mode:
                    p = by_title.get(title)
                    if p:
                        RegionalTournamentProblem.objects.create(tournament=reg, problem=p)
            # mode is None → no problems (pending placeholder)

            n = RegionalTournamentProblem.objects.filter(
                tournament=reg, problem__page=cur
            ).count()
            self.stdout.write(
                f"{'+' if created else '~'} {slug} {reg.region_code} problems={n} when={reg.when_label()!r}"
            )

        publish_page(page, user=None, summary="Региональные турниры 2026/27: полный список")
        self.stdout.write(self.style.SUCCESS(f"Done: {page.regions.count()} tournaments"))
