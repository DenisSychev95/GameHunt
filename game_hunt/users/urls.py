from django.urls import path, reverse_lazy
from . import views
from allauth.account.views import PasswordChangeView
from django.views.generic import TemplateView

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile-view/<str:pk>', views.profile_view, name='profile-view'),

    # После успешной смены пароля делаем редирект на профиль
    path('password/change/', PasswordChangeView.as_view(success_url=reverse_lazy('account_change_password_done')),
         name='account_change_password'),
    path("password/change/done/", TemplateView.as_view(template_name="account/password_change_done.html"),
         name="account_change_password_done",),
    path('email/confirmed/', TemplateView.as_view(template_name='account/email_confirmed.html'),
         name='account_email_confirmed'),

    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path("profile/image/edit/", views.profile_image_edit, name="profile_image_edit"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:pk>/detail/", views.notification_detail, name="notification_detail"),
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),

    path("admin-messages/", views.admin_messages_inbox, name="admin_messages_inbox"),
    path("admin-messages/<int:pk>/detail/", views.admin_message_detail, name="admin_message_detail"),
    path("admin-messages/<int:pk>/read/", views.admin_message_mark_read, name="admin_message_mark_read"),
    path("contact-admin/", views.contact_admin, name="contact_admin"),
    path("admin-send-message/", views.admin_send_message, name="admin_send_message"),
    path("notifications/<int:pk>/hide/", views.notification_unpublish, name="notification_unpublish"),
    path("admin-messages/<int:pk>/hide/", views.admin_message_unpublish, name="admin_message_unpublish"),

]

