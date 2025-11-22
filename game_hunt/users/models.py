from django.db import models
from django.contrib.auth.models import User
from django.db.models import OneToOneField
from datetime import date, timedelta
from django.utils import timezone


# Создаем модель профиля пользователя
class Profile(models.Model):

    user = OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    nickname = models.CharField(blank=True, max_length=100, verbose_name='Никнейм')
    # Добавить стандартную картинку профиля
    profile_image = models.ImageField(null=True, default='default.png', upload_to='profile_images/',
                                      verbose_name='Картинка профиля')
    bio = models.TextField(blank=True, verbose_name='О себе')
    birth_date = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    phone = models.CharField(blank=True, max_length=15, verbose_name='Телефон')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Зарегистрирован')
    updated = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    is_banned = models.BooleanField(default=False, verbose_name='Заблокирован')
    last_seen = models.DateTimeField(blank=True, null=True, verbose_name='Последняя активность')

    def __str__(self):

        return self.nickname

    # Геттер для установления возраста пользователя
    @property
    def age(self):
        if not self.birth_date:
            return None
        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    # Геттер для проверки совершеннолетия
    @property
    def is_adult(self):
        age = self.age
        return age is not None and age >= 18

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    # Геттер для получения флага онлайн/оффлайн(пользователь онлайн если был активен в течение 5 минут)
    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return timezone.now() - self.last_seen < timedelta(minutes=5)
