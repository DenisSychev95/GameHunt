from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    # --- Админка на сайте --- #
    # ------ url главной страницы админки
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    # ------ url добавления игры
    path('admin-panel/games/add/', views.admin_game_create, name='admin_game_create'),
    # ------ url редактирования игры
    path('admin-panel/games/<int:pk>/edit/', views.admin_game_edit, name='admin_game_edit'),
    # ------ url удаления игры
    path('admin-panel/games/<int:pk>/delete/', views.admin_game_delete, name='admin_game_delete'),
    # ------ url комментариев пользователя игры
    path('admin-panel/users/<int:user_id>/comments/',
         views.admin_user_comments, name='admin_user_comments'),
    # ------ url бан/разбан пользователя
    path('admin-panel/users/<int:user_id>/toggle-ban/',
         views.admin_toggle_ban, name='admin_toggle_ban'),
]
