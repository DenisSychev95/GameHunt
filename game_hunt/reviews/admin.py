from django.contrib import admin
from .models import Review, ReviewImage, ReviewVote, ReviewComment
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms


class ReviewAdminForm(forms.ModelForm):
    text = forms.CharField(widget=CKEditorUploadingWidget(), label='Содержание')

    class Meta:
        model = Review
        fields = "__all__"


class ReviewImageInline(admin.StackedInline):
    model = ReviewImage
    extra = 0
    ordering = ('order',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = ("title", "created_at", "game", "author", "is_published_status", "rating",  "views_count",
                    "liked_percent_str",)
    list_display_links = ("title",)
    list_filter = ("is_published", "rating", "created_at")
    search_fields = ("title", "game__title", "author__username")
    inlines = [ReviewImageInline]
    actions = ["publish_selected", "unpublish_selected"]

    def is_published_status(self, obj):
        if obj.is_published:
            return 'Да ✅'

        return 'Нет ⛔️'
    is_published_status.short_description = 'Опубликовано'

    def liked_percent_str(self, obj):
        return f'{obj.liked_percent} %'

    liked_percent_str.short_description = 'Понравилось'


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
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


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
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

