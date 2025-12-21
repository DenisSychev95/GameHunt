from django.urls import path
from . import views


urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('<slug:slug>/', views.game_detail, name='game_detail'),
    path('<slug:slug>/vote/', views.game_vote, name='game_vote'),
    path('<slug:slug>/comment/add/', views.game_add_comment, name='game_add_comment'),
    path('comments/<int:pk>/delete/', views.game_comment_delete, name='game_comment_delete'),
    path('comments/<int:pk>/edit/', views.game_comment_edit, name='game_comment_edit'),

]