from django.utils import timezone
from .models import Profile


# при запуске сервера создается экземпляр класса LastSeenMiddleware
class LastSeenMiddleware:
    def __init__(self, get_responce):
        self.get_responce = get_responce

    # отрабатывает при каждом запросе пользователя, т.к он включён в MIDDLEWARE settings.py
    def __call__(self, request):
        response = self.get_responce(request)
        # для авторизированного пользователя находим экземпляр Profile через filter(быстрее, не выдаст ошибку),
        # затем обновляем last_seen экземпляра Profile через update
        if request.user.is_authenticated:
            Profile.objects.filter(user=request.user).update(last_seen=timezone.now())
        return response
