from django.db import models
from django.contrib.auth.models import User
from django.db.models import OneToOneField
from datetime import date, timedelta
from django.utils import timezone
# Забираем из нашего encryption шифрующее поле.
from . encryption import EncryptedCharField, EncryptedDateField
# Импортировали нашу модель с жанрами
from games.models import Genre
from django.conf import settings


# Создаем модель профиля пользователя.
class Profile(models.Model):

    user = OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    nickname = models.CharField(max_length=150, db_index=True, unique=True, verbose_name='Никнейм')
    # Далее шифруемые поля Profile.
    first_name = EncryptedCharField(blank=True, null=True, max_length=150, verbose_name='Имя')
    last_name = EncryptedCharField(blank=True, null=True, max_length=150, verbose_name='Фамилия')
    email = EncryptedCharField(blank=True, null=True, max_length=250, verbose_name='Почта')
    birth_date = EncryptedDateField(blank=True, null=True, verbose_name='Дата рождения')
    phone = EncryptedCharField(blank=True, null=True, max_length=25, unique=True, verbose_name='Телефон')
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


ADMIN_MESSAGE_CHOICES_GUEST = [
    ("complaint", "Жалоба"),
    ("site_bug", "Ошибка на сайте"),
    ("suggestion", "Предложение"),
    ("account_restore", "Восстановление аккаунта"),
    ("other", "Другое"),
]

ADMIN_MESSAGE_CHOICES_AUTH = [
    ("complaint", "Жалоба"),
    ("site_bug", "Ошибка на сайте"),
    ("suggestion", "Предложение"),
    ("question", "Вопрос"),
    ("content_moderation", "Модерация контента"),
    ("other", "Другое"),
]

USER_MESSAGE_CHOICES = [
    ("warning", "Предупреждение"),
    ("moderation_result", "Результаты модерации"),
    ("profile_block", "Блокировка профиля"),
    ("sanctions", "Санкции"),
    ("other", "Другое"),
]

ADMIN_TOPIC_CHOICES = [
    ("complaint", "Жалоба"),
    ("site_bug", "Ошибка на сайте"),
    ("suggestion", "Предложение"),
    ("account_restore", "Восстановление аккаунта"),
    ("question", "Вопрос"),
    ("content_moderation", "Модерация контента"),
    ("other", "Другое"),
]

ADMIN_STATUS_CHOICES = [
    ("created", "Создано"),
    ("in_review", "На рассмотрении"),
    ("moderation", "На модерации"),
    ("processed", "Обработано"),
]


class AdminMessages(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')

    # отправитель: либо user, либо гость
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="admin_messages", verbose_name='Отправитель'
    )
    guest_name = models.CharField(max_length=120, blank=True, verbose_name='Гость(имя)')
    guest_email = models.EmailField(blank=True, verbose_name='Гость(email)')

    topic = models.CharField(max_length=40, choices=ADMIN_TOPIC_CHOICES, default="other", verbose_name="Тема")
    # валидируем формой
    topic_custom = models.CharField(max_length=120, blank=True, verbose_name='Своя тема обращения')

    message = models.TextField(verbose_name='Текст обращения')
    image = models.ImageField(
        upload_to="user_messages/",
        blank=True,
        null=True,
        verbose_name="Изображение"
    )
    is_published = models.BooleanField(default=True, verbose_name="Показывать")
    status = models.CharField(
        max_length=20,
        choices=ADMIN_STATUS_CHOICES,
        default="created",
        verbose_name="Статус",
    )

    class Meta:
        ordering = ["is_read", "-created_at"]  # непрочитанные сверху
        verbose_name = 'Сообщение для администрации'
        verbose_name_plural = 'Сообщения для администрации'

    def __str__(self):
        who = self.user.username if self.user_id else (self.guest_name or self.guest_email or "guest")
        return f"{who}: {self.topic}"


class UserMessages(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_messages", verbose_name='Получатель'
    )

    sender = models.CharField(max_length=120, default="Администрация сайта", verbose_name='Отправитель')
    topic = models.CharField(max_length=40, choices=USER_MESSAGE_CHOICES, default="other", verbose_name='Тема сообщения')
    title = models.CharField(max_length=140, verbose_name='Своя тема обращения', blank=True)
    text = models.TextField(verbose_name='Текст сообщения')
    link = models.CharField(max_length=255, blank=True, verbose_name='Ссылка')
    image = models.ImageField(
        upload_to="user_messages/",
        blank=True,
        null=True,
        verbose_name="Изображение"
    )
    is_published = models.BooleanField(default=True, verbose_name="Показывать")

    class Meta:
        ordering = ["is_read", "-created_at"]
        verbose_name = 'Уведомление для пользователя'
        verbose_name_plural = 'Уведомления для пользователей'

    def __str__(self):
        return f"{self.user.username}: {self.title}"