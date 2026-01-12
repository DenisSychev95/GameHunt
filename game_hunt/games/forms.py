from django import forms
from .models import GameComment
from .models import Game, GameImage
from datetime import date
from django.forms import inlineformset_factory


class GameCommentForm(forms.ModelForm):
    class Meta:
        model = GameComment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={
                "class": "gd-textarea",
                "placeholder": "Оставьте комментарий…",
                "rows": 6,
                "maxlength": 500,
            })
        }


class GameAdminForm(forms.ModelForm):
    class Meta:
        model = Game
        exclude = ('views_count',)
        widgets = {
            'release_date': forms.SelectDateWidget(
                years=range(date.today().year, date.today().year - 40, -1)
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # вешаем класс admin-input на ВСЕ поля формы
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            # аккуратно добавляем наш класс, не затирая предыдущие
            field.widget.attrs['class'] = (existing + ' admin-input').strip()


# Вот он — inline formset: “несколько ReviewImage для одного Review”
GameImageFormSet = inlineformset_factory(
    parent_model=Game,
    model=GameImage,
    fields=("image", "caption", "position"),
    extra=5,         # покажем 0 пустых формы под новые картинки
    can_delete=True  # можно удалить существующую картинку
)