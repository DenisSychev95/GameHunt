from django.db import models
from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User
from django.utils.text import slugify


# Модель для Разработчика
class Developer(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='Разработчик')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='Слаг')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'разработчик'
        verbose_name_plural = 'разработчики'
        ordering = ['name']


# Модель для Издателя
class Publisher(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='Издатель')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='Слаг')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'издатель'
        verbose_name_plural = 'издатели'
        ordering = ['name']


# Модель для жанров
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Жанр')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'жанр'
        verbose_name_plural = 'жанры'
        ordering = ['name']

    def __str__(self):
        return self.name


# Модель для платформ
class Platform(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Платформа')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'платформа'
        verbose_name_plural = 'платформы'
        ordering = ['name']

    def __str__(self):
        return self.name


# Модель для игр
class Game(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название игры')
    slug = models.SlugField(max_length=220, unique=True, verbose_name='Слаг')
    description = models.TextField(verbose_name='Описание')
    release_date = models.DateField(blank=True, null=True, verbose_name='Дата выхода')

    genres = models.ManyToManyField(Genre, related_name='games', blank=True, verbose_name='Жанры')
    platforms = models.ManyToManyField(Platform, related_name='games', blank=True, verbose_name='Платформы')

    is_adult_only = models.BooleanField(default=False, verbose_name='Контент 16+')
    cover_image = models.ImageField(
        upload_to='game_covers/',
        default='default_game_cover.jpg',
        blank=True,
        null=True,
        verbose_name='Обложка'
    )

    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Опубликована на сайте')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')
    developer = models.ForeignKey(Developer, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_query_name='games', verbose_name='Разработчик')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_query_name='games', verbose_name='Издатель')

    avg_rating = models.DecimalField(blank=True, max_digits=3, decimal_places=1, default=0,
                                     verbose_name="Средний рейтинг")
    liked_percent = models.PositiveSmallIntegerField(blank=True, default=0, verbose_name="Понравилось")
    trailer_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на трейлер (YouTube/Vimeo)"
    )

    class Meta:
        verbose_name = 'игра'
        verbose_name_plural = 'игры'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # если слаг не задан — он генерируется автоматически
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    def recalc_stats(self):
        """
        Пересчитывает avg_rating и liked_percent по обзорам.
        liked_percent = доля обзоров с rating >= 7 (можешь поменять порог).
        """
        qs = self.reviews.filter(is_published=True)

        agg = qs.aggregate(
            avg=Avg("rating"),
            total=Count("id"),
            liked=Count("id", filter=Q(rating__gte=7)),
        )

        total = agg["total"] or 0
        avg = agg["avg"] or 0

        self.avg_rating = round(float(avg), 1)
        self.liked_percent = int(round((agg["liked"] / total) * 100)) if total else 0
        self.save(update_fields=["avg_rating", "liked_percent"])

    def recalc_liked_percent(self):
        """
        liked_percent = процент лайков среди всех голосов
        """
        votes = self.votes.all()

        agg = votes.aggregate(
            total=Count('id'),
            likes=Count('id', filter=Q(value=GameVote.LIKE)),
        )

        total = agg['total'] or 0

        if total > 0:
            self.liked_percent = round((agg['likes'] / total) * 100)
        else:
            self.liked_percent = 0

        self.save(update_fields=['liked_percent'])

    def avg_rating_display(self):
        return f"{self.avg_rating}/10"

    def liked_percent_display(self):
        return f"{self.liked_percent}%"

    # получаем виртуальное поле по связанной модели GameVote через related_name - счетчик лайков для игры
    @property
    def likes_count(self):
        return self.votes.filter(value=1).count()  # получили количество полей value где, было выбрано(LIKE, 'Лайк')

    # получаем виртуальное поле по связанной модели GameVote через related_name- счетчик дизлайков для игры
    @property
    def dislikes_count(self):
        return self.votes.filter(value=-1).count()
        # получили количество полей value где, было выбрано(DISLIKE, 'Дизлайк')


class GameImage(models.Model):
    game = models.ForeignKey(
        "Game",
        on_delete=models.CASCADE,
        related_name="gallery",
        verbose_name="Игра"
    )
    image = models.ImageField(upload_to="game_gallery/", verbose_name="Добавить изображение")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Описание")
    position = models.PositiveIntegerField(default=1, verbose_name="Номер картинки")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "картинка для"
        verbose_name_plural = "картинки игры"
        ordering = ["position",]

    def __str__(self):
        return f"{self.game.title} — №{self.position}"


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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_votes', verbose_name='Пользователь')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='votes', verbose_name='Игра')
    # Поле выбора для лайка/дизлайка предлагает 2 варианта на выбор
    value = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name='Оценка')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        # Уникальные пары: один user голосует за игру только 1 раз
        unique_together = ('user', 'game')
        verbose_name = 'оценка игры'
        verbose_name_plural = 'оценки игр'

    def __str__(self):
        # Возвращаем человеко-читаемое представление какой user какую игру как оценил
        # + строковое представление из VOTE_CHOICES
        return f'{self.user} оценил {self.game} -  и поставил {self.get_value_display()}'


# Модель комментария для игры
class GameComment(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='comments', verbose_name='Игра')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_comments', verbose_name='Пользователь')
    text = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалён')
    is_edited = models.BooleanField(default=False, verbose_name='Изменен')

    class Meta:
        verbose_name = 'комментарий к игре'
        verbose_name_plural = 'комментарии к играм'
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий от {self.user} к {self.game}'