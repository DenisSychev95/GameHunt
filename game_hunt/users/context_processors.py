from .models import AdminMessages, UserMessages


def bell_counts(request):
    admin_unread = 0
    user_unread = 0

    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            admin_unread = AdminMessages.objects.filter(is_read=False).count()

        # ✅ считаем для любого пользователя, включая админов
        user_unread = UserMessages.objects.filter(user=request.user, is_read=False).count()

    return {
        "admin_unread_count": admin_unread,
        "user_unread_count": user_unread,
        "bell_total": admin_unread + user_unread,
    }