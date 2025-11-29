from django.urls import path, reverse_lazy
from . import views
from allauth.account.views import PasswordChangeView
from django.views.generic import TemplateView

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    # После успешной смены пароля делаем редирект на профиль
    path('password/change/', PasswordChangeView.as_view(success_url=reverse_lazy('profile')),
         name='account_change_password'),
    path('email/confirmed/', TemplateView.as_view(template_name='account/email_confirmed.html'),
         name='account_email_confirmed'),

    path('profile/edit/', views.profile_edit, name='profile_edit'),

]

