from django.db import models
from django.contrib.auth.models import User
from games.models import Game


class Walkthrough(models.Model):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='walkthroughs',
        verbose_name='Игра'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='walkthroughs',
        verbose_name='Автор'
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(max_length=220, unique=True, verbose_name='Slug')
    content = models.TextField(verbose_name='Текст прохождения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')

    class Meta:
        verbose_name = 'прохождение'
        verbose_name_plural = 'прохождения'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.game}'
