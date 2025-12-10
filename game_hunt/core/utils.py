
# Вспомогательная функция для проверки доступа пользователя к админ-панели

def staff_check(user):
    return user.is_staff or user.is_superuser
