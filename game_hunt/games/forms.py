from django import forms
from .models import GameComment
from .models import Game
from datetime import date


class GameCommentForm(forms.ModelForm):
    class Meta:
        model = GameComment
        fields = ('text',)
        labels = {
            'text': 'Комментарий',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
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
