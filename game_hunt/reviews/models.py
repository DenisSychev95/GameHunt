from django.db import models
from django.contrib.auth.models import User
from games.models import Game


class Review(models.Model):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Игра'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор'
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст обзора')
    rating = models.PositiveSmallIntegerField(
        default=10,
        verbose_name='Оценка',
        help_text='От 1 до 10'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    is_published = models.BooleanField(default=True, verbose_name='Опубликован')

    class Meta:
        verbose_name = 'обзор'
        verbose_name_plural = 'обзоры'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.game}'

