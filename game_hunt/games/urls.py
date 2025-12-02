from django.urls import path
from . import views


urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('<slug:slug>/', views.game_detail, name='game_detail'),
    path('<slug:slug>/vote/<str:value>/', views.game_vote, name='game_vote'),
]