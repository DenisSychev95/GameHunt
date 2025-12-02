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
        fields = '__all__'
        widgets = {
            'release_date': forms.SelectDateWidget(
                years=range(date.today().year, date.today().year - 40, -1)
            )
        }
