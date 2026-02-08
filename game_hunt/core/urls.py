from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path("rules/", TemplateView.as_view(template_name="core/rules.html"), name="rules"),

    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),


    path('admin-panel/games/add/', views.admin_game_create, name='admin_game_create'),
    path('admin-panel/games/<int:pk>/edit/', views.admin_game_edit, name='admin_game_edit'),
    path('admin-panel/games/<int:pk>/delete/', views.admin_game_delete, name='admin_game_delete'),


    path('admin-panel/users/<int:user_id>/comments/',
         views.admin_user_comments, name='admin_user_comments'),


    path('admin-panel/users/<int:user_id>/toggle-ban-ajax/',
         views.admin_toggle_ban_ajax, name='admin_toggle_ban_ajax'),


    path('admin-panel/users/<int:user_id>/toggle-ban/',
         views.admin_toggle_ban, name='admin_toggle_ban'),
    path('admin-panel/reviews/add/', views.admin_review_create, name='admin_review_create'),
    path("admin-panel/reviews/<int:pk>/edit/", views.admin_review_edit, name="admin_review_edit"),

    path("admin-panel/walkthroughs/add/", views.admin_walkthrough_create, name="admin_walkthrough_create"),
    path("admin-panel/walkthroughs/<slug:slug>/edit/", views.admin_walkthrough_edit, name="admin_walkthrough_edit"),
    path("admin-panel/cheats/create/", views.admin_cheat_create, name="admin_cheat_create"),

]
