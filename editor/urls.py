from django.urls import path

from editor import views

app_name = "editor"

urlpatterns = [
    path("vhod/", views.login_view, name="login"),
    path("vyhod/", views.logout_view, name="logout"),
    path("priglashenie/<str:code>/", views.register_view, name="register"),
    path("priglasheniya/", views.invites, name="invites"),
    path("priglasheniya/<int:pk>/otozvat/", views.invite_revoke, name="invite_revoke"),
    path("", views.dashboard, name="dashboard"),
    path("zhurnal/", views.journal, name="journal"),
    path("zhurnal/<int:pk>/", views.journal_detail, name="journal_detail"),
    path("sezony/novyy/", views.season_create, name="season_create"),
    path("sezony/otkryt-novyy/", views.season_open_new, name="season_open_new"),
    path("sezony/<int:year>/", views.season_detail, name="season_detail"),
    path("sezony/<int:year>/meta/", views.season_meta, name="season_meta"),
    path("sezony/<int:year>/v-proshedshie/", views.season_archive, name="season_archive"),
    path("sezony/<int:year>/sdelat-tekushchim/", views.season_make_current, name="season_make_current"),
    # Задачи
    path("sezony/<int:year>/zadachi/", views.season_problems, name="season_problems"),
    path("sezony/<int:year>/zadachi/dobavit/", views.problem_add, name="problem_add"),
    path("sezony/<int:year>/zadachi/<int:pk>/", views.problem_edit, name="problem_edit"),
    path("sezony/<int:year>/zadachi/<int:pk>/udalit/", views.problem_delete, name="problem_delete"),
    path("sezony/<int:year>/skany/dobavit/", views.scan_add, name="scan_add"),
    path("sezony/<int:year>/skany/<int:pk>/udalit/", views.scan_delete, name="scan_delete"),
    # Результаты
    path("sezony/<int:year>/rezultaty/", views.season_results, name="season_results"),
    path("sezony/<int:year>/rezultaty/stroka/", views.result_row_add, name="result_row_add"),
    path("sezony/<int:year>/rezultaty/stroka/<int:pk>/", views.result_row_edit, name="result_row_edit"),
    path("sezony/<int:year>/rezultaty/stroka/<int:pk>/udalit/", views.result_row_delete, name="result_row_delete"),
    path("sezony/<int:year>/rezultaty/ssylka/", views.results_more_save, name="results_more_save"),
    path("sezony/<int:year>/rezultaty/ochistit/", views.results_clear, name="results_clear"),
    # IYPT
    path("sezony/<int:year>/iypt/", views.season_iypt, name="season_iypt"),
    path("sezony/<int:year>/iypt/stroka/", views.iypt_row_add, name="iypt_row_add"),
    path("sezony/<int:year>/iypt/stroka/<int:pk>/udalit/", views.iypt_row_delete, name="iypt_row_delete"),
    # Фото
    path("sezony/<int:year>/foto/", views.season_photos, name="season_photos"),
    path("sezony/<int:year>/foto/dobavit/", views.photo_add, name="photo_add"),
    path("sezony/<int:year>/foto/<int:pk>/udalit/", views.photo_delete, name="photo_delete"),
    # Материалы
    path("sezony/<int:year>/materialy/", views.season_materials, name="season_materials"),
    path("sezony/<int:year>/materialy/dobavit/", views.link_add, name="link_add"),
    path("sezony/<int:year>/materialy/<int:pk>/udalit/", views.link_delete, name="link_delete"),
    # Турниры в России
    path("rossiya/", views.russia_list, name="russia_list"),
    path("rossiya/novyy/", views.russia_edit, name="russia_add"),
    path("rossiya/<int:pk>/", views.russia_edit, name="russia_edit"),
    path("rossiya/<int:pk>/udalit/", views.russia_delete, name="russia_delete"),
]
