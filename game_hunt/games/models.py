from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# Модель для жанров
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Жанр')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name


# Модель для платформ
class Platform(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Платформа')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Платформа'
        verbose_name_plural = 'Платформы'
        ordering = ['name']

    def __str__(self):
        return self.name


# Модель для игр
class Game(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=220, unique=True, verbose_name='Слаг')
    description = models.TextField(verbose_name='Описание')
    release_date = models.DateField(blank=True, null=True, verbose_name='Дата выхода')

    genres = models.ManyToManyField(Genre, related_name='games', blank=True, verbose_name='Жанры')
    platforms = models.ManyToManyField(Platform, related_name='games', blank=True, verbose_name='Платформы')

    is_adult_only = models.BooleanField(default=False, verbose_name='Контент 18+')
    cover_image = models.ImageField(
        upload_to='game_covers/',
        default='default_game_cover.jpg',
        blank=True,
        null=True,
        verbose_name='Обложка'
    )

    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлена')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # если слаг не задан — он генерируется  автоматически
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    # получаем виртуальное поле по связанной модели GameVote через related_name - счетчик лайков для игры
    @property
    def likes_count(self):
        return self.votes.filter(value=1).count()  # получили количество полей value где, было выбрано(LIKE, 'Лайк')

    # получаем виртуальное поле по связанной модели GameVote через related_name- счетчик дизлайков для игры
    @property
    def dislikes_count(self):
        return self.votes.filter(value=-1).count()
        # получили количество полей value где, было выбрано(DISLIKE, 'Дизлайк')


# Модель отданных голосов за игру
class GameVote(models.Model):
    # Значения констант вариантов выбора
    LIKE = 1
    DISLIKE = -1
    # Варианты на выбор: лайк/дизлайк(кортеж: значение-текстовое представление)
    VOTE_CHOICES = (
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_votes')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='votes')
    # Поле выбора для лайка/дизлайка предлагает 2 варианта на выбор
    value = models.SmallIntegerField(choices=VOTE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Уникальные пары: один user голосует за игру только 1 раз
        unique_together = ('user', 'game')
        verbose_name = 'Оценка игры'
        verbose_name_plural = 'Оценки игр'

    def __str__(self):
        # Возвращаем человеко-читаемое представление какой user какую игру как оценил
        # + строковое представление из VOTE_CHOICES
        return f'{self.user} -> {self.game} ({self.get_value_display()})'


# Модель комментария для игры
class GameComment(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_comments')
    text = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалён')

    class Meta:
        verbose_name = 'Комментарий к игре'
        verbose_name_plural = 'Комментарии к играм'
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий от {self.user} к {self.game}'