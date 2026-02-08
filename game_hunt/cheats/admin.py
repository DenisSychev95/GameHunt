from django.contrib import admin
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model

from .models import Cheat, CheatVote, CheatComment

User = get_user_model()


class UserNickChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nick = ""
        try:
            nick = (obj.profile.nickname or "").strip()
        except Exception:
            pass
        return f"{nick} ({obj.username})" if nick and nick != obj.username else obj.username


class CheatAdminForm(forms.ModelForm):
    author = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label="Автор",
    )

    class Meta:
        model = Cheat
        fields = "__all__"


@admin.register(Cheat)
class CheatAdmin(admin.ModelAdmin):
    form = CheatAdminForm
    save_on_top = True

    list_display = (
        "title",
        "updated_at",
        "game",
        "author_nick",
        "platform",
        "is_published_status",
        "views_count",
        "downloads_count",
        "liked_percent_str",
        "get_small_cover",
    )
    list_display_links = ("title",)
    list_filter = ("is_published", "platform", "updated_at")
    search_fields = ("title", "game__title", "author__username", "author__profile__nickname", "slug")
    ordering = ("-updated_at",)

    fields = (
        "title",
        "slug",
        "game",
        "author",
        ("cover_image", "get_big_cover"),
        "platform",
        "functionality",
        "instruction",
        "notes",
        "cheat_file",
        "is_published",
        "views_count",
        "downloads_count",
        "liked_percent",
        "created_at",
        "updated_at",
    )

    readonly_fields = (
        "get_big_cover",
        "views_count",
        "downloads_count",
        "liked_percent",
        "created_at",
        "updated_at",
    )

    def author_nick(self, obj):
        try:
            return obj.author.profile.nickname or obj.author.username
        except Exception:
            return obj.author.username
    author_nick.short_description = "Автор(ник)"
    author_nick.admin_order_field = "author__username"

    def is_published_status(self, obj):
        return "Да ✅" if obj.is_published else "Нет ⛔️"
    is_published_status.short_description = "Опубликован"

    def liked_percent_str(self, obj):
        return f"{obj.liked_percent} %"
    liked_percent_str.short_description = "Понравилось"

    def get_small_cover(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="70">')
        # если у тебя есть дефолт, оставь так; иначе можно вернуть пусто
        return mark_safe(f'<img src="{settings.MEDIA_URL}default_game_cover.jpg" width="70">')
    get_small_cover.short_description = "Обложка"

    def get_big_cover(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="200">')
        return ""
    get_big_cover.short_description = "Превью"


@admin.register(CheatVote)
class CheatVoteAdmin(admin.ModelAdmin):
    list_display = ("user_nick", "cheat", "value")
    list_filter = ("value",)
    search_fields = ("user__username", "user__profile__nickname", "cheat__title")

    def user_nick(self, obj):
        try:
            return obj.user.profile.nickname or obj.user.username
        except Exception:
            return obj.user.username
    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"


@admin.register(CheatComment)
class CheatCommentAdmin(admin.ModelAdmin):
    list_display = ("user_nick", "cheat", "created_at", "admin_deleted_status")
    list_filter = ("is_deleted", "created_at")
    search_fields = ("text", "user__username", "user__profile__nickname", "cheat__title")
    ordering = ("-created_at",)

    def user_nick(self, obj):
        try:
            return obj.user.profile.nickname or obj.user.username
        except Exception:
            return obj.user.username
    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"

    def admin_deleted_status(self, obj):
        return "Нет ✅" if not obj.is_deleted else "Да ⛔️"
    admin_deleted_status.short_description = "Удалён"