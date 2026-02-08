from django.urls import path
from . import views

urlpatterns = [
    path("", views.cheat_list, name="cheat_list"),

    path("add/", views.cheat_create, name="cheat_create"),
    path("add/<slug:game_slug>/", views.cheat_create_for_game, name="cheat_create_for_game"),
    path("<slug:slug>/", views.cheat_detail, name="cheat_detail"),
    path("<slug:slug>/edit/", views.cheat_edit, name="cheat_edit"),
    path("<slug:slug>/delete/", views.cheat_delete, name="cheat_delete"),

    path("<slug:slug>/vote/", views.cheat_vote, name="cheat_vote"),
    path("<slug:slug>/comments/add/", views.cheat_add_comment, name="cheat_add_comment"),
    path("comments/<int:pk>/delete/", views.cheat_comment_delete, name="cheat_comment_delete"),
    path("comments/<int:pk>/edit/", views.cheat_comment_edit, name="cheat_comment_edit"),
    path("<slug:slug>/download/", views.cheat_download, name="cheat_download"),
]