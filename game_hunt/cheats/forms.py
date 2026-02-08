from django import forms

from .models import Cheat, CheatComment
from reviews.widgets import SimpleClearableFileInput, SimpleClearableFileCheat


SCROLL_FIELDS = {'functionality', 'instruction', 'notes'}


class CheatAdminPanelCreateForm(forms.ModelForm):

    class Meta:
        model = Cheat
        fields = (
            "game",
            "title",
            "cover_image",
            "platform",
            "functionality",
            "instruction",
            "notes",
            "cheat_file",
        )
        widgets = {
            "cover_image": SimpleClearableFileInput(),
            "cheat_file": SimpleClearableFileCheat(),
            "functionality": forms.Textarea(attrs={"rows": 5}),
            "instruction": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            classes = ["gd-field-control"]

            if isinstance(field.widget, forms.Textarea):
                classes.append("gd-textarea")

            if name in SCROLL_FIELDS:
                classes.append("gd-review-scroll")

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()


class CheatFormStaffCreateForGame(forms.ModelForm):
    class Meta:
        model = Cheat
        fields = (
            "title",
            "cover_image",
            "platform",
            "functionality",
            "instruction",
            "notes",
            "cheat_file",
        )
        widgets = {
            "cover_image": SimpleClearableFileInput(),
            "cheat_file": SimpleClearableFileCheat(),
            "functionality": forms.Textarea(attrs={"rows": 5}),
            "instruction": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            classes = ["gd-field-control"]
            if isinstance(field.widget, forms.Textarea):
                classes.append("gd-textarea")

            # вертикальный scroll (только для textarea-полей)
            if name in SCROLL_FIELDS:
                classes.append("gd-review-scroll")

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()


class CheatFormAdminCreate(forms.ModelForm):
    """
    Создание чита с нуля (только админ/стафф).
    Выбор игры есть.
    """
    class Meta:
        model = Cheat
        fields = (
            "game",
            "title",
            "cover_image",
            "platform",
            "functionality",
            "instruction",
            "notes",
            "cheat_file",
            "is_published",
        )
        widgets = {
            "cover_image": SimpleClearableFileInput(),
            "cheat_file": SimpleClearableFileInput(),
            "functionality": forms.Textarea(attrs={"rows": 5}),
            "instruction": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            classes = ["gd-field-control"]

            if isinstance(field.widget, forms.Textarea):
                classes.append("gd-textarea")

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()


class CheatFormAdminEdit(forms.ModelForm):

    class Meta:
        model = Cheat
        fields = (
            "title",
            "cover_image",
            "platform",
            "functionality",
            "instruction",
            "notes",
            "cheat_file",
            "is_published",
        )

        widgets = {
            "cover_image": SimpleClearableFileInput(),
            "cheat_file": SimpleClearableFileCheat(),
            "functionality": forms.Textarea(attrs={"rows": 5}),
            "instruction": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            classes = ["gd-field-control"]

            if isinstance(field.widget, forms.Textarea):
                classes.append("gd-textarea")

                # вертикальный scroll (только для textarea-полей)
            if name in SCROLL_FIELDS:
                classes.append("gd-review-scroll")

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()


class CheatCommentForm(forms.ModelForm):
    """
    Комментарий к читу (как в прохождениях).
    """
    class Meta:
        model = CheatComment
        fields = ("text",)
        labels = {"text": "Комментарий"}
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        existing = self.fields["text"].widget.attrs.get("class", "")
        self.fields["text"].widget.attrs["class"] = (existing + " gd-field-control gd-textarea").strip()