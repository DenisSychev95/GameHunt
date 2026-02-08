from django.db import models
from django.contrib.auth.models import User
from games.models import Game
from django.db.models import Avg, Count, Q


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Игра"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Автор"
    )

    title = models.CharField(max_length=200, verbose_name="Название")

    # Структура
    summary = models.TextField(
        blank=True,
        verbose_name="Краткое описание",
    )

    text = models.TextField(verbose_name="Содержание обзора")
    pros = models.TextField(blank=True, verbose_name="Понравилось")
    cons = models.TextField(blank=True, verbose_name="Не понравилось")
    conclusion = models.TextField(blank=True, verbose_name="Итоги")

    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name="Оценка"
    )

    video_url = models.URLField(
        blank=True,
        verbose_name="Ссылка на видео"
    )

    # Для модерации
    is_published = models.BooleanField(default=False, verbose_name="Опубликован")
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    liked_percent = models.PositiveSmallIntegerField(blank=True, default=0, verbose_name="Понравилось")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")
    cover_image = models.ImageField(upload_to='review_covers/', blank=True, null=True, verbose_name="Обложка обзора")

    class Meta:
        verbose_name = "обзор"
        verbose_name_plural = "обзоры"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.game}"

    def recalc_liked_percent(self):
        """
        liked_percent = процент лайков среди всех голосов
        """
        votes = self.votes.all()

        agg = votes.aggregate(
            total=Count('id'),
            likes=Count('id', filter=Q(value=ReviewVote.LIKE)),
        )

        total = agg['total'] or 0

        if total > 0:
            self.liked_percent = round((agg['likes'] / total) * 100)
        else:
            self.liked_percent = 0

        self.save(update_fields=['liked_percent'])

    def liked_percent_display(self):
        return f"{self.liked_percent}%"


# Модель отданных голосов за обзор
class ReviewVote(models.Model):
    # Значения констант вариантов выбора
    LIKE = 1
    DISLIKE = -1
    # Варианты на выбор: лайк/дизлайк(кортеж: значение-текстовое представление)
    VOTE_CHOICES = (
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_votes', verbose_name='Пользователь')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes', verbose_name='Обзор')
    # Поле выбора для лайка/дизлайка предлагает 2 варианта на выбор
    value = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name='Оценка')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        # Уникальные пары: один user голосует за игру только 1 раз
        unique_together = ('user', 'review')
        verbose_name = 'оценка обзора'
        verbose_name_plural = 'оценки обзоров'

    def __str__(self):
        # Возвращаем человеко-читаемое представление какой user какую игру как оценил
        # + строковое представление из VOTE_CHOICES
        return f'{self.user} -> {self.review} ({self.get_value_display()})'


# Модель комментария для обзора
class ReviewComment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments', verbose_name='Обзор')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_comments', verbose_name='Пользователь')
    text = models.TextField(max_length=500, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалён')
    is_edited = models.BooleanField(default=False, verbose_name='Изменен')

    class Meta:
        verbose_name = 'комментарий к игре'
        verbose_name_plural = 'комментарии к обзорам'
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий от {self.user} к {self.review.game}'


class ReviewImage(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="review_images/", verbose_name="Добавить изображение")
    caption = models.CharField(max_length=200, blank=True, verbose_name="Описание")
    order = models.PositiveSmallIntegerField(default=1, verbose_name="Номер картинки")

    class Meta:
        ordering = ["order",]
        verbose_name = "картинка для обзора"
        verbose_name_plural = "картинка для обзоров"

    def __str__(self):
        return f"{self.review.title[:30]}... - №{self.order}"

