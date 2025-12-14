from django.urls import path
from . import views

urlpatterns = [
    path('', views.walkthrough_list, name='walkthrough_list'),
    path('<slug:slug>/', views.walkthrough_detail, name='walkthrough_detail'),
    path('game/<slug:game_slug>/add/', views.walkthrough_create, name='walkthrough_create'),
]