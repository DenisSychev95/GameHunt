from django import forms
from .models import Review, ReviewImage
from django.forms import inlineformset_factory


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = [
            "title",
            "summary",
            "text",
            "pros",
            "cons",
            "conclusion",
            "rating",
            "video_url",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "Заголовок обзора"
            }),
            "summary": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Кому подойдёт игра? Кому нет?"
            }),
            "text": forms.Textarea(attrs={
                "rows": 8,
                "placeholder": "Основной текст обзора"
            }),
            "pros": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Что понравилось (каждый пункт с новой строки)"
            }),
            "cons": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Что не понравилось"
            }),
            "conclusion": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Финальный вывод"
            }),
            "rating": forms.Select(),  # ← ВАЖНО: dropdown
            "video_url": forms.URLInput(attrs={
                "placeholder": "https://youtube.com/..."
            }),
        }


# Вот он — inline formset: “несколько ReviewImage для одного Review”
ReviewImageFormSet = inlineformset_factory(
    parent_model=Review,
    model=ReviewImage,
    fields=("image", "caption", "order"),
    extra=3,         # покажем 3 пустых формы под новые картинки
    can_delete=True  # можно удалить существующую картинку
)
