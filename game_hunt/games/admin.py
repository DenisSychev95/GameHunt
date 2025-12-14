from django.contrib import admin
from .models import Genre, Platform, Game, GameVote, GameComment, Developer, Publisher
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
    list_display = ('name',)
    # автозаполняемые поля(слаг генерируется из поля name этой модели)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name',)
    # автозаполняемые поля( слаг генерируется из поля name этой модели)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    form = GameAdminForm
    list_display = ('title', 'is_adult_only', 'views_count', 'created_at', "release_date", "developer", "publisher")
    list_filter = ('is_adult_only', 'genres', 'platforms', 'release_date', "developer", "publisher")
    search_fields = ('title', "developer__name", "publisher__name")
    # автозаполняемые поля( слаг генерируется из поля title этой модели)
    prepopulated_fields = {'slug': ('title',)}
    # Добавляем фильтр на странице списка объектов в админке по возрасту, по жанру
    filter_horizontal = ('genres', 'platforms')


@admin.register(GameVote)
class GameVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'value', 'created_at')
    # Добавляем фильтр на странице списка объектов в админке по лайку/дизлайку
    list_filter = ('value',)


@admin.register(GameComment)
class GameCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'created_at', 'is_deleted')
    #  Добавляем фильтр на странице списка объектов в админке по времени создания, удален или нет
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('text',)