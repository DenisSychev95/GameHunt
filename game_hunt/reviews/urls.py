from django.urls import path
from . import views

urlpatterns = [
    # Список всех обзоров (+ фильтр по игре через ?game=<slug>)
    path('', views.review_list, name='review_list'),

    # Детальная страница обзора
    path('<int:pk>/', views.review_detail, name='review_detail'),

    # Создание обзора для конкретной игры
    path('game/<slug:game_slug>/add/', views.review_create, name='review_create'),
    # Редактирование обзора для конкретной игры
    path('<int:pk>/edit/', views.review_edit, name='review_edit'),
    # Удаление обзора для конкретной игры
    path('<int:pk>/delete/', views.review_delete, name='review_delete'),
]
