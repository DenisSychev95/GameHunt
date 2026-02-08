from django.contrib import admin
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import Walkthrough, WalkthroughImage, WalkthroughVote, WalkthroughComment

User = get_user_model()


class UserNickChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nick = ""
        try:
            nick = (obj.profile.nickname or "").strip()
        except Exception:
            pass
        return f"{nick} ({obj.username})" if nick and nick != obj.username else obj.username


class WalkthroughAdminForm(forms.ModelForm):
    text = forms.CharField(widget=CKEditorUploadingWidget(), label="Содержание")

    author = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label="Автор",
    )

    class Meta:
        model = Walkthrough
        fields = "__all__"


class WalkthroughImageInline(admin.StackedInline):
    model = WalkthroughImage
    extra = 0
    ordering = ("order",)
    fields = ("caption", ("image", "get_small_img"), "order")
    readonly_fields = ("get_small_img",)

    def get_small_img(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100">')
        return ""
    get_small_img.short_description = "Миниатюра"


@admin.register(Walkthrough)
class WalkthroughAdmin(admin.ModelAdmin):
    form = WalkthroughAdminForm
    inlines = [WalkthroughImageInline]
    save_on_top = True

    list_display = (
        "title",
        "created_at",
        "game",
        "author_nick",
        "is_published_status",
        "views_count",
        "liked_percent_str",
        "get_small_img",
    )
    list_display_links = ("title",)
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "game__title", "author__username", "author__profile__nickname")
    ordering = ("-created_at",)

    fields = (
        "title",
        "author",
        "game",
        "is_published",
        ("cover_image", "get_small_cover"),
        "summary",
        "text",
        "video_url",
    )
    readonly_fields = ("get_small_cover",)

    actions = ["publish_selected", "unpublish_selected"]

    def author_nick(self, obj):
        try:
            return obj.author.profile.nickname or obj.author.username
        except Exception:
            return obj.author.username
    author_nick.short_description = "Автор(ник)"
    author_nick.admin_order_field = "author__username"

    def is_published_status(self, obj):
        return "Да ✅" if obj.is_published else "Нет ⛔️"
    is_published_status.short_description = "Опубликовано"

    def liked_percent_str(self, obj):
        return f"{obj.liked_percent} %"
    liked_percent_str.short_description = "Понравилось"

    def get_small_img(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="70">')
        return mark_safe(f'<img src="{settings.MEDIA_URL}default_game_cover.jpg" width="70">')
    get_small_img.short_description = "Миниатюра обложки"

    def get_small_cover(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="200">')
        return mark_safe(f'<img src="{settings.MEDIA_URL}default_game_cover.jpg" width="200">')
    get_small_cover.short_description = "Обложка"

    def publish_selected(self, request, queryset):
        queryset.update(is_published=True)
    publish_selected.short_description = "Опубликовать выбранные"

    def unpublish_selected(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_selected.short_description = "Снять с публикации"


@admin.register(WalkthroughVote)
class WalkthroughVoteAdmin(admin.ModelAdmin):
    list_display = ("user", "walkthrough", "value")
    list_filter = ("value",)
    search_fields = ("user__username", "user__profile__nickname", "walkthrough__title")


@admin.register(WalkthroughComment)
class WalkthroughCommentAdmin(admin.ModelAdmin):
    list_display = ("user_nick", "walkthrough", "created_at", "admin_deleted_status")
    list_filter = ("is_deleted", "created_at")
    search_fields = ("text", "user__username", "user__profile__nickname", "walkthrough__title")

    def user_nick(self, obj):
        try:
            return obj.user.profile.nickname or obj.user.username
        except Exception:
            return obj.user.username
    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"

    def admin_deleted_status(self, obj):
        return "Нет ✅" if not obj.is_deleted else "Да ⛔️"
    admin_deleted_status.short_description = "Удалён с сайта"