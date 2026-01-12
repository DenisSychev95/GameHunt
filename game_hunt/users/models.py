from django.db import models
from django.contrib.auth.models import User
from django.db.models import OneToOneField
from datetime import date, timedelta
from django.utils import timezone
# Забираем из нашего encryption шифрующее поле.
from . encryption import EncryptedCharField, EncryptedDateField
# Импортировали нашу модель с жанрами
from games.models import Genre


# Создаем модель профиля пользователя.
class Profile(models.Model):

    user = OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    nickname = models.CharField(blank=True, max_length=100, verbose_name='Никнейм')
    # Далее шифруемые поля Profile.
    first_name = EncryptedCharField(blank=True, null=True, max_length=150, verbose_name='Имя')
    last_name = EncryptedCharField(blank=True, null=True, max_length=150, verbose_name='Фамилия')
    email = EncryptedCharField(blank=True, null=True, max_length=250, verbose_name='Почта')
    birth_date = EncryptedDateField(blank=True, null=True, verbose_name='Дата рождения')
    phone = EncryptedCharField(blank=True, null=True, max_length=15, unique=True, verbose_name='Телефон')
    # Далее не шифруемые поля Profile.
    # Добавить стандартную картинку профиля
    profile_image = models.ImageField(null=True, default='default.png', upload_to='profile_images/',
                                      verbose_name='Картинка профиля')
    bio = models.TextField(blank=True, verbose_name='О себе')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Зарегистрирован')
    updated = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    is_banned = models.BooleanField(default=False, verbose_name='Заблокирован')
    last_seen = models.DateTimeField(blank=True, null=True, verbose_name='Последняя активность')
    # Добавляем поле любимые жанры
    favorite_genres = models.ManyToManyField(Genre, blank=True, related_name='fans', verbose_name='Любимые жанры')

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

    # Геттер для проверки 16+
    @property
    def is_adult(self):
        age = self.age
        return age is not None and age >= 16

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'
        ordering = ['created',]

    # Геттер для получения флага онлайн/оффлайн(пользователь онлайн если был активен в течение 5 минут)
    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return timezone.now() - self.last_seen < timedelta(minutes=5)
