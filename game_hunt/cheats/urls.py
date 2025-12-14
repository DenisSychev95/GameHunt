from django.urls import path
from . import views

urlpatterns = [
    path('', views.cheat_list, name='cheat_list'),
    path('<int:pk>/', views.cheat_detail, name='cheat_detail'),
    path('game/<slug:game_slug>/add/', views.cheat_create, name='cheat_create'),
]