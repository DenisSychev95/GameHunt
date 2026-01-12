from django.urls import path
from . import views

urlpatterns = [
    path("", views.review_list, name="review_list"),
    path("<int:pk>/", views.review_detail, name="review_detail"),

    path("game/<slug:game_slug>/add/", views.review_create, name="review_create"),
    path("<int:pk>/edit/", views.review_edit, name="review_edit"),
    path("<int:pk>/delete/", views.review_delete, name="review_delete"),

    path('comments/<int:pk>/edit/', views.review_comment_edit, name='review_comment_edit'),
    path("comments/<int:pk>/delete/", views.review_comment_delete, name="review_comment_delete"),
    path('<int:pk>/vote/', views.review_vote, name='review_vote'),
    path('<int:pk>/comment/add/', views.review_add_comment, name='review_add_comment'),
]