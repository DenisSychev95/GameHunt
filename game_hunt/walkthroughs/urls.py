from django.urls import path
from . import views

urlpatterns = [
    path("", views.walkthrough_list, name="walkthrough_list"),

    path("game/<slug:game_slug>/add/", views.walkthrough_create, name="walkthrough_create"),

    path("<slug:slug>/", views.walkthrough_detail, name="walkthrough_detail"),
    path("<slug:slug>/edit/", views.walkthrough_edit, name="walkthrough_edit"),
    path("<slug:slug>/delete/", views.walkthrough_delete, name="walkthrough_delete"),

    path("<slug:slug>/vote/", views.walkthrough_vote, name="walkthrough_vote"),
    path("<slug:slug>/comments/add/", views.walkthrough_add_comment, name="walkthrough_add_comment"),
    path("comments/<int:pk>/delete/", views.walkthrough_comment_delete, name="walkthrough_comment_delete"),
    path("comments/<int:pk>/edit/", views.walkthrough_comment_edit, name="walkthrough_comment_edit"),
]