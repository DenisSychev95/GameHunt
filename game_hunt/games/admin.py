from django.contrib import admin
from .models import Genre, Platform, Game, GameVote, GameComment, Developer, Publisher, GameImage
from . forms import GameAdminForm
from django.utils.safestring import mark_safe
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


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', "slug")
    # автозаполняемые поля(слаг генерируется из поля name этой модели)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', "slug")
    # автозаполняемые поля( слаг генерируется из поля name этой модели)
    prepopulated_fields = {'slug': ('name',)}


class GameImageInline(admin.StackedInline):
    model = GameImage
    extra = 0
    fields = ('caption', ('image', 'get_small_img'), 'position', )
    readonly_fields = ('get_small_img', )
    ordering = ('position', )

    def get_small_img(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100">')

    get_small_img.short_description = 'Миниатюра'


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    form = GameAdminForm
    list_display = ('title', 'created_at', 'views_count', 'avg_rating', 'age_status', 'get_small_img',)
    list_filter = ('is_adult_only', 'genres', 'platforms',)
    search_fields = ('title',)
    fields = (('title', 'slug'), 'release_date', 'description', 'is_adult_only', ('developer', 'publisher'),
              'genres', 'platforms', ('cover_image', 'get_small_cover'), 'trailer_url')
    readonly_fields = ('get_small_cover',)
    # автозаполняемые поля( слаг генерируется из поля title этой модели)
    prepopulated_fields = {'slug': ('title',)}
    # Добавляем фильтр на странице списка объектов в админке по возрасту, по жанру
    filter_horizontal = ('genres', 'platforms')
    inlines = [GameImageInline]
    save_on_top = True

    def age_status(self, obj):
        if obj.is_adult_only:
            return 'Да ⛔️'

        return 'Нет ✅'

    age_status.short_description = 'Контент 16+'

    def get_small_img(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="70">')

    get_small_img.short_description = 'Миниатюра обложки'

    def get_small_cover(self, obj):
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" width="200">')

    get_small_cover.short_description = "Миниатюра обложки"


class GameVoteAdminForm(forms.ModelForm):
    user = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Пользователь',
    )

    class Meta:
        model = GameVote
        fields = "__all__"


@admin.register(GameVote)
class GameVoteAdmin(admin.ModelAdmin):
    form = GameVoteAdminForm
    list_display = ('user_nick', 'game', 'created_at', 'admin_show_value', )
    # Добавляем фильтр на странице списка объектов в админке по лайку/дизлайку
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


class GameCommentAdminForm(forms.ModelForm):
    user = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Пользователь',
    )

    class Meta:
        model = GameComment
        fields = "__all__"


@admin.register(GameComment)
class GameCommentAdmin(admin.ModelAdmin):
    form = GameCommentAdminForm
    list_display = ('user_nick', 'game', 'created_at', 'admin_deleted_status')
    #  Добавляем фильтр на странице списка объектов в админке по времени создания, удален или нет
    list_filter = ('is_deleted', 'created_at')
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
