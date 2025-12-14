from django.db import models
from games.models import Game


class Cheat(models.Model):
    PLATFORM_CHOICES = [
        ('pc', 'PC'),
        ('ps', 'PlayStation'),
        ('xbox', 'Xbox'),
        ('switch', 'Nintendo Switch'),
        ('other', 'Другое'),
    ]

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='cheats',
        verbose_name='Игра'
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='pc',
        verbose_name='Платформа'
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    code = models.TextField(verbose_name='Код / последовательность действий')
    description = models.TextField(blank=True, verbose_name='Описание / комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')

    class Meta:
        verbose_name = 'чит'
        verbose_name_plural = 'читы'
        ordering = ['game', 'platform', 'title']

    def __str__(self):
        return f'{self.title} ({self.game})'