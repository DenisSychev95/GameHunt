from django.contrib import admin
from .models import Review, ReviewImage, ReviewVote, ReviewComment
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()


class UserNickChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nick = ""
        try:
            nick = (obj.profile.nickname or "").strip()
        except Exception:
            pass

        # ✅ ник первым, username для различения
        if nick and nick != obj.username:
            return f"{nick} ({obj.username})"
        return obj.username


class ReviewAdminForm(forms.ModelForm):
    text = forms.CharField(widget=CKEditorUploadingWidget(), label='Содержание')
    author = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Автор',
    )

    class Meta:
        model = Review
        fields = "__all__"


class ReviewImageInline(admin.StackedInline):
    model = ReviewImage
    extra = 0
    ordering = ('order',)
    fields = ('caption', ('image', 'get_small_img'), 'order',)
    readonly_fields = ('get_small_img',)

    def get_small_img(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100">')

    get_small_img.short_description = 'Миниатюра'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = ("title", "created_at", "game", "user_nick", "is_published_status", "rating",  "views_count",
                    "liked_percent_str", 'get_small_img',)
    list_display_links = ("title",)
    list_filter = ("is_published", "rating", "created_at")
    fields = ('title', 'author', 'game', 'is_published', ('cover_image', 'get_small_cover'), 'summary',
              'text', ('pros', 'cons',), 'conclusion', 'video_url', 'rating')
    readonly_fields = ('get_small_cover',)
    search_fields = ("title", "game__title", "author__username", 'author__profile__nickname')
    inlines = [ReviewImageInline]
    actions = ["publish_selected", "unpublish_selected"]
    save_on_top = True

    def is_published_status(self, obj):
        if obj.is_published:
            return 'Да ✅'

        return 'Нет ⛔️'
    is_published_status.short_description = 'Опубликовано'

    def liked_percent_str(self, obj):
        return f'{obj.liked_percent} %'

    liked_percent_str.short_description = 'Понравилось'

    def get_small_img(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="70">')
        return mark_safe(
            f'<img src="{settings.MEDIA_URL}default_game_cover.jpg" width="70">'

        )

    get_small_img.short_description = "Миниатюра обложки"

    def get_small_cover(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="200">')
        return mark_safe(
            f'<img src="{settings.MEDIA_URL}default_game_cover.jpg" width="200">')

    get_small_cover.short_description = "Миниатюра обложки"

    def user_nick(self, obj):
        # ник у тебя всегда есть, но fallback на username оставим
        return obj.author.profile.nickname or obj.author.username

    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"


class ReviewVoteAdminForm(forms.ModelForm):
    user = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Автор',
    )

    class Meta:
        model = Review
        fields = "__all__"


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    form = ReviewVoteAdminForm
    list_display = (
        'user_nick',
        'review',
        'created_at',
        'admin_show_value',
    )

    list_filter = ('value',)

    def admin_show_value(self, obj):
        if obj.value == 1:
            return '👍🏻'
        return '👎🏻'

    admin_show_value.short_description = 'Оценка'

    def user_nick(self, obj):
        # ник у тебя всегда есть, но fallback на username оставим
        return obj.user.profile.nickname or obj.user.username

    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"


class ReviewCommentAdminForm(forms.ModelForm):
    user = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Автор',
    )

    class Meta:
        model = Review
        fields = "__all__"


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    form = ReviewCommentAdminForm
    list_display = (
        'user_nick',
        'review',
        'created_at',
        'admin_deleted_status',
    )

    # фильтры
    list_filter = ('is_deleted', 'created_at')

    # поиск по тексту комментария
    search_fields = ('text',)

    def admin_deleted_status(self, obj):
        if not obj.is_deleted:
            return 'Нет ✅'
        return 'Да ⛔️'

    admin_deleted_status.short_description = 'Удалён с сайта'

    def user_nick(self, obj):
        # ник у тебя всегда есть, но fallback на username оставим
        return obj.user.profile.nickname or obj.user.username

    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"