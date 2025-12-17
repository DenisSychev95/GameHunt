from django.db import models
from django.contrib.auth.models import User
from games.models import Game


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

    title = models.CharField(max_length=200, verbose_name="Заголовок")

    # Структура
    summary = models.TextField(
        blank=True,
        verbose_name="Коротко (TL;DR)",
        help_text="1–3 предложения: кому зайдёт, кому нет"
    )
    text = models.TextField(verbose_name="Основной текст обзора")
    pros = models.TextField(blank=True, verbose_name="Плюсы")
    cons = models.TextField(blank=True, verbose_name="Минусы")
    conclusion = models.TextField(blank=True, verbose_name="Итог")

    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name="Оценка"
    )

    video_url = models.URLField(
        blank=True,
        verbose_name="Ссылка на видео (YouTube / VK / Rutube)"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")
    is_published = models.BooleanField(default=True, verbose_name="Опубликован")
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')

    class Meta:
        verbose_name = "обзор"
        verbose_name_plural = "обзоры"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.game}"


class ReviewImage(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="review_images/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "изображение обзора"
        verbose_name_plural = "изображения обзора"

    def __str__(self):
        return f"Image for review {self.review_id}"
