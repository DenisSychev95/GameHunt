from django.contrib import admin
from .models import Genre, Platform, Game, GameVote, GameComment, Developer, Publisher, GameImage
from . forms import GameAdminForm


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
    fields = ('caption', 'image', 'position', )
    ordering = ('position', )


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    form = GameAdminForm
    list_display = ('title', 'created_at', 'views_count', 'avg_rating', 'age_status', )
    list_filter = ('is_adult_only', 'genres', 'platforms',)
    search_fields = ('title',)
    # автозаполняемые поля( слаг генерируется из поля title этой модели)
    prepopulated_fields = {'slug': ('title',)}
    # Добавляем фильтр на странице списка объектов в админке по возрасту, по жанру
    filter_horizontal = ('genres', 'platforms')
    inlines = [GameImageInline]

    def age_status(self, obj):
        if obj.is_adult_only:
            return 'Да ⛔️'

        return 'Нет ✅'

    age_status.short_description = 'Контент 16+'


@admin.register(GameVote)
class GameVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'created_at', 'admin_show_value', )
    # Добавляем фильтр на странице списка объектов в админке по лайку/дизлайку
    list_filter = ('value',)

    def admin_show_value(self, obj):
        if obj.value == 1:
            return '👍🏻'
        return '👎🏻'

    admin_show_value.short_description = 'Оценка'


@admin.register(GameComment)
class GameCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'created_at', 'admin_deleted_status')
    #  Добавляем фильтр на странице списка объектов в админке по времени создания, удален или нет
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('text',)

    def admin_deleted_status(self, obj):
        if not obj.is_deleted:
            return 'Нет ✅'

        return 'Да ⛔️'

    admin_deleted_status.short_description = 'Удалён с сайта'
