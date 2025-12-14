from django import forms
from .models import Cheat


class CheatForm(forms.ModelForm):
    class Meta:
        model = Cheat
        fields = ['platform', 'title', 'code', 'description']