"""Пересобрать страницу «Сборник видео» с нормальной разметкой ссылок."""

from django.core.management.base import BaseCommand

from home.models import MaterialPage

# Чистая разметка: заголовки + списки, короткие подписи к ссылкам (без сырых URL в тексте).
BODY = """
<p>Сборник ссылок на общедоступные материалы в интернете. Актуально на 23.09.2026. Благодарим авторов всех видео.</p>

<h2>Архив Турнира юных физиков</h2>
<ul>
<li>IYPT Archive (Илья Марченко) — <a href="https://archive.iypt.org">сайт</a></li>
</ul>

<h2>О турнире для новичков</h2>
<ul>
<li>Вебинар Всероссийского ТЮФ — <a href="https://vkvideo.ru/video-222342853_456239068">видео</a>, <a href="https://rosypt.glas.su/vvodnyj-vebinar-19-09-09-21">текст</a></li>
</ul>

<h2>Методические материалы и вебинары</h2>
<ul>
<li>17 видео о турнире (Клим Сладков, Анна Макарова) — <a href="https://teach-in.ru/course/young-physicists-tournament">Teach-in</a>, <a href="https://www.youtube.com/playlist?list=PLW8KJ94kzB1U">YouTube</a></li>
<li>Плейлист GetAClass о ТЮФ — <a href="https://youtube.com/playlist?list=PLeOlm2kq0HcuFuxsSVnWhrW4XJkH6IJFd">YouTube</a></li>
<li>Разбор действия (Алексей Кротов) — <a href="https://youtu.be/cmv7P-zi4PA">видео</a></li>
<li>Как попадают на IYPT (Иван Ильин, Vectozavr) — <a href="https://www.youtube.com/watch?v=yOOBL-swqxI">видео</a></li>
<li>«Идеальное преступление» (пример, как делать не надо) — <a href="https://vkvideo.ru/video29058065_456239047">видео</a></li>
<li>Командообразование и роль капитана (Мария Буда) — <a href="https://vkvideo.ru/video-222342853_456239033">видео</a></li>
<li>Как подготовить команду к ТЮФ (Клим Сладков) — <a href="https://vkvideo.ru/video-222342853_456239019">видео</a></li>
<li>О физическом эксперименте (Александра Ким) — <a href="https://m.vkvideo.ru/video-222342853_456239069">видео</a>, <a href="https://disk.yandex.com/i/Y5b93YusrQ1vpQ">Яндекс Диск</a>, <a href="https://rosypt.glas.su/o-fizicheskom-eksperimente-09-28">текст</a></li>
<li>Читаем научные статьи (Иван Полоник) — <a href="https://vkvideo.ru/video-222342853_456239070">видео</a>, <a href="https://disk.yandex.com/i/R7v5ufHG_ugKrg">Яндекс Диск</a>, <a href="https://rosypt.glas.su/vebinar-chitaem-nauchnye-stat-i-10-03">текст</a></li>
<li>Построение теоретической модели (Александр Зинкевич) — <a href="https://vkvideo.ru/video-222342853_456239072?list=a74825c166622c622a">видео</a>, <a href="https://1drv.ms/v/c/baa78f7e03504d87/IQDBXf0bW4T4RLHD8zT9eMAnAS26YnjAKvZSIk5Dhg4Uqw4?e=vPFJai">OneDrive</a>, <a href="https://rosypt.glas.su/postroenie-teoreticheskoj-modeli-10-11">текст</a></li>
<li>Доклад и эксперимент (Никита Карпенко-Черников) — <a href="https://vkvideo.ru/video-222342853_456239020">видео</a></li>
<li>Оппонирование и рецензирование (Артём Голомолзин) — <a href="https://vkvideo.ru/video-222342853_456239020">видео</a></li>
<li>Andrei Klishin Keynote — подготовка доклада — <a href="https://www.youtube.com/watch?v=9-yyAml67Aw">видео</a></li>
<li>Съезд учителей физики в МГУ, 2011 (Юносов, Львовский) — <a href="https://www.youtube.com/watch?v=QLNpd_g386E">видео</a></li>
</ul>

<h2>Видеозаписи боёв</h2>
<h3>Русский язык</h3>
<ul>
<li>Архив Ришельевского лицея — <a href="https://www.youtube.com/playlist?list=PL94693C48BB763D71">плейлист</a></li>
<li>Финалы Минского городского ТЮФ — <a href="https://www.youtube.com/watch?v=7tCfqx-465k">2022</a>, <a href="https://youtu.be/BuM46bKj6U8">2023</a></li>
<li>Финал СибТЮФ 2022 — <a href="https://youtu.be/jhZQeXUYw-U">видео</a></li>
<li>Финал МосГорТЮФ 2026 — <a href="https://www.youtube.com/watch?v=t8kz50X9wFQ">видео</a></li>
<li>Финал 47-го Всероссийского ТЮФ 2025 — <a href="https://vkvideo.ru/video-222342853_456239017">видео</a></li>
<li>Финал Всероссийского ТЮФ 2018 — <a href="https://vkvideo.ru/video-44049348_456239026">часть 1</a>, <a href="https://vkvideo.ru/video-44049348_456239028">часть 2</a></li>
<li>Финал Белорусского (республиканского) ТЮФ 2022 — <a href="https://www.youtube.com/watch?v=cldpPXVKwV0">видео</a></li>
<li>Всероссийский ТЮФ 2016, 1-й отборочный бой — <a href="https://www.youtube.com/watch?v=2Wm0e9WjNe8">видео</a></li>
<li>Доклад Егора Закутея (2020), Лига физиков — <a href="https://vkvideo.ru/video-169307964_456239027">видео</a></li>
<li>Доклад Ивана Свинцова (2020), Лига физиков — <a href="https://vkvideo.ru/video-169307964_456239029">видео</a></li>
</ul>
<h3>Английский язык</h3>
<ul>
<li>Финалы IYPT — <a href="https://youtu.be/uZcSHyajcQE">2023</a>, <a href="https://youtu.be/cwp8NLzAeGQ">2026</a></li>
<li>5-й бой IYPT 2017 — <a href="https://www.youtube.com/watch?v=G0B7zZq3d1s">видео</a></li>
<li>Поиск на YouTube — <a href="https://www.youtube.com/results?search_query=IYPT">IYPT</a>, <a href="https://www.youtube.com/results?search_query=young+physicists+tournament">Young Physicists Tournament</a></li>
<li>Канал канадского ТЮФ — <a href="https://www.youtube.com/@canadianyoungphysiciststou9723">YouTube</a></li>
<li>Финал 7-го IPT — <a href="https://vkvideo.ru/video-102517808_171627814">видео</a></li>
</ul>

<h2>О заданиях, физике и инструментах</h2>
<ul>
<li>Reference Kit — <a href="https://kit.ilyam.org">сайт</a></li>
<li>Павел Виктор, «Из архивов ТЮФ» — <a href="https://www.youtube.com/playlist?list=PL1Us50cZo25n-BAoac7vqcO2GNUuvVtjM">плейлист</a></li>
<li>Канал GetAClass — <a href="https://www.youtube.com/@getaclassphys">YouTube</a></li>
<li>Tracker и Origin (Александра Ким) — <a href="https://vkvideo.ru/video-132197226_456239501">видео</a></li>
<li>Видео об Origin (Егор Волощук) — <a href="https://vkvideo.ru/video-237696303_456239021">видео</a></li>
<li>Мастер-классы «Живая физика» — <a href="https://youtube.com/playlist?list=PLxa4rguca7ht2hSfoFLnvVjySIGYRQM">плейлист</a></li>
<li>Мастер-классы Algodoo — <a href="https://youtube.com/playlist?list=PLxAIHjnWyfeEZWxgm6mYF2eAnmU-eyipJ">плейлист</a></li>
<li>Цвет на графике (Александра Ким) — <a href="https://vkvideo.ru/video-132197226_456239521">видео</a></li>
<li>Плейлист PASCO (Сибирский ТЮФ) — <a href="https://vk.ru/playlist/-19771285_55403368">VK</a></li>
<li>Обсуждения заданий в группе СибТЮФ — <a href="https://vk.ru/board19771285">доска</a></li>
<li>Научная литература (Александр Светличный) — <a href="https://vkvideo.ru/video-102636970_456239129">видео</a></li>
<li>Канал IYPT Sweden — <a href="https://www.youtube.com/watch?v=a8VxgY6PyOg">видео</a></li>
</ul>

<h2>Об организации</h2>
<ul>
<li>О ТЮФ для организаторов (Никита Карпенко-Черников) — <a href="https://drive.google.com/file/d/1SRb-55RtFszd1aIvWCpm6dTvNoOfczp2/view?usp=drive_link">презентация</a></li>
<li>Турнир как игра (Клим Сладков) — <a href="https://drive.google.com/file/d/1CFetJvJ-C1M7IoALRe3xPh-gHAlh3jcR/view?usp=drive_link">презентация</a></li>
<li>Менеджер турнирной информации (Антон Иванов) — <a href="https://drive.google.com/file/d/1P7aeRQBLxFwk6rTiw6hMt98fm5d7k29/view?usp=drive_link">презентация</a></li>
<li>Гайд по фандрайзингу (конференция организаторов) — <a href="https://drive.google.com/file/d/1z2AdDxphB-Cc5xafQEj1II0ZMWqlyOkP/view">документ</a></li>
</ul>
""".strip()


class Command(BaseCommand):
    help = "Обновить разметку страницы «Сборник видео»"

    def handle(self, *args, **options):
        page = (
            MaterialPage.objects.filter(slug="sbornik-video").first()
            or MaterialPage.objects.filter(title__icontains="Сборник видео").first()
        )
        if not page:
            self.stderr.write("Страница «Сборник видео» не найдена.")
            return
        page.body = BODY
        page.save_revision().publish()
        self.stdout.write(self.style.SUCCESS(f"Обновлено: {page.title} ({page.url})"))
