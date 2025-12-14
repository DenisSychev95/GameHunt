from django import forms
from .models import Walkthrough


class WalkthroughForm(forms.ModelForm):
    class Meta:
        model = Walkthrough
        fields = ['title', 'content']