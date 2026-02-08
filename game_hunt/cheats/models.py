from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Q
from slugify import slugify

from games.models import Game


def unique_slugify(instance, base: str, slug_field: str = "slug"):
    Model = instance.__class__
    slug = base
    n = 2
    while Model.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class Cheat(models.Model):
    # ⚠️ platform оставь свои choices (если они уже есть в проекте) — здесь пример:
    PLATFORM_CHOICES = (
        ("pc", "PC"),
        ("ps", "PlayStation"),
        ("xbox", "Xbox"),
        ("switch", "Switch"),
        ("mobile", "Mobile"),
        ("other", "Другое"),
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="cheats",
        verbose_name="Игра",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cheats",
        verbose_name="Автор",
    )

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=220, unique=True, db_index=True, blank=True, verbose_name="Слаг")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    cover_image = models.ImageField(
        upload_to="cheat_covers/",
        blank=True,
        null=True,
        verbose_name="Обложка",
    )

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default="pc",
        verbose_name="Платформа",
    )

    functionality = models.TextField(blank=True, verbose_name="Функционал")
    instruction = models.TextField(blank=True, verbose_name="Инструкция")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    cheat_file = models.FileField(
        upload_to="cheat_files/",
        blank=True,
        null=True,
        verbose_name="Файл чита/тренера",
    )

    is_published = models.BooleanField(default=True, verbose_name="Опубликован")

    views_count = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    liked_percent = models.PositiveSmallIntegerField(blank=True, default=0, verbose_name="Понравилось")
    downloads_count = models.PositiveIntegerField(default=0, verbose_name="Скачивания")

    class Meta:
        verbose_name = "чит"
        verbose_name_plural = "читы"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} — {self.game}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            self.slug = unique_slugify(self, base)
        super().save(*args, **kwargs)

    def recalc_liked_percent(self):
        votes = self.votes.all()

        agg = votes.aggregate(
            total=Count("id"),
            likes=Count("id", filter=Q(value=CheatVote.LIKE)),
        )
        total = agg["total"] or 0
        self.liked_percent = round((agg["likes"] / total) * 100) if total > 0 else 0
        self.save(update_fields=["liked_percent"])


class CheatVote(models.Model):
    LIKE = 1
    DISLIKE = -1

    VOTE_CHOICES = (
        (LIKE, "Лайк"),
        (DISLIKE, "Дизлайк"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cheat_votes", verbose_name="Пользователь")
    cheat = models.ForeignKey(Cheat, on_delete=models.CASCADE, related_name="votes", verbose_name="Чит")
    value = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name="Оценка")

    class Meta:
        unique_together = ("user", "cheat")
        verbose_name = "оценка чита"
        verbose_name_plural = "оценки читов"

    def __str__(self):
        return f"{self.user} → {self.cheat} ({self.get_value_display()})"


class CheatComment(models.Model):
    cheat = models.ForeignKey(Cheat, on_delete=models.CASCADE, related_name="comments", verbose_name="Чит")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cheat_comments", verbose_name="Пользователь")
    text = models.TextField(max_length=500, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалён")
    is_edited = models.BooleanField(default=False, verbose_name="Отредактирован")

    class Meta:
        verbose_name = "комментарий к читу"
        verbose_name_plural = "комментарии к читам"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Комментарий от {self.user} к {self.cheat}"