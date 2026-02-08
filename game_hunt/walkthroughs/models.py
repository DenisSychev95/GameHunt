from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Q
from games.models import Game
from slugify import slugify  # python-slugify


def unique_slugify(instance, base: str, slug_field: str = "slug"):
    """
    Делает уникальный slug: base, base-2, base-3...
    """
    Model = instance.__class__
    slug = base
    n = 2
    while Model.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class Walkthrough(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="walkthroughs", verbose_name="Игра")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="walkthroughs", verbose_name="Автор")

    title = models.CharField(max_length=200, verbose_name="Название")

    # ✅ если поле slug уже есть — приведи к этому, иначе добавь
    slug = models.SlugField(
        max_length=220,
        unique=True,
        db_index=True,
        blank=True,
        verbose_name="Слаг",
    )

    summary = models.TextField(blank=True, verbose_name="Краткое описание")
    text = models.TextField(verbose_name="Содержание прохождения", blank=True, null=True)
    video_url = models.URLField(blank=True, verbose_name="Ссылка на видео", max_length=3000)

    is_published = models.BooleanField(default=False, verbose_name="Опубликован")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    liked_percent = models.PositiveSmallIntegerField(blank=True, default=0, verbose_name="Понравилось")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    cover_image = models.ImageField(
        upload_to="walkthrough_covers/",
        blank=True,
        null=True,
        verbose_name="Обложка прохождения",
    )

    class Meta:
        verbose_name = "прохождение"
        verbose_name_plural = "прохождения"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.game}"

    def save(self, *args, **kwargs):
        # ✅ генерируем slug при создании/если пустой
        if not self.slug:
            base = slugify(self.title)  # русское -> latin
            self.slug = unique_slugify(self, base)
        super().save(*args, **kwargs)

    def recalc_liked_percent(self):
        votes = self.votes.all()
        agg = votes.aggregate(
            total=Count("id"),
            likes=Count("id", filter=Q(value=WalkthroughVote.LIKE)),
        )
        total = agg["total"] or 0
        self.liked_percent = round((agg["likes"] / total) * 100) if total > 0 else 0
        self.save(update_fields=["liked_percent"])


class WalkthroughVote(models.Model):
    LIKE = 1
    DISLIKE = -1

    VOTE_CHOICES = (
        (LIKE, "Лайк"),
        (DISLIKE, "Дизлайк"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="walkthrough_votes", verbose_name="Пользователь")
    walkthrough = models.ForeignKey(Walkthrough, on_delete=models.CASCADE, related_name="votes", verbose_name="Прохождение")
    value = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name="Оценка")

    class Meta:
        unique_together = ("user", "walkthrough")
        verbose_name = "оценка прохождения"
        verbose_name_plural = "оценки прохождений"

    def __str__(self):
        return f"{self.user} → {self.walkthrough} ({self.get_value_display()})"


class WalkthroughComment(models.Model):
    walkthrough = models.ForeignKey(Walkthrough, on_delete=models.CASCADE, related_name="comments", verbose_name="Прохождение")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="walkthrough_comments", verbose_name="Пользователь")
    text = models.TextField(max_length=500, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалён")
    is_edited = models.BooleanField(default=False, verbose_name="Изменен")

    class Meta:
        verbose_name = "комментарий к прохождению"
        verbose_name_plural = "комментарии к прохождениям"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Комментарий от {self.user} к {self.walkthrough}"


class WalkthroughImage(models.Model):
    walkthrough = models.ForeignKey(
        Walkthrough,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Прохождение",
    )
    image = models.ImageField(upload_to="walkthrough_images/", verbose_name="Добавить изображение")
    caption = models.CharField(max_length=200, blank=True, verbose_name="Описание")
    order = models.PositiveSmallIntegerField(default=1, verbose_name="Номер картинки")

    class Meta:
        ordering = ["order"]
        verbose_name = "картинка для прохождения"
        verbose_name_plural = "картинки для прохождений"

    def __str__(self):
        return f"Картинка #{self.order} для {self.walkthrough}"