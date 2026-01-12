from django import forms
from .models import Review, ReviewImage, ReviewComment
from django.forms import inlineformset_factory
from ckeditor_uploader.widgets import CKEditorUploadingWidget


SCROLL_FIELDS = {'summary', 'text', 'conclusion'}


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = (
            "title",
            "summary",
            "text",
            "video_url",
            "pros",
            "cons",
            "conclusion",
            "rating",
        )
        widgets = {
            "text": CKEditorUploadingWidget(),  # CKEditor только тут
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            classes = ["gd-field-control"]  # ширина 85% + margin 10 auto

            # textarea базовый
            if isinstance(field.widget, forms.Textarea):
                classes.append("gd-textarea")

            # вертикальный scroll (только для textarea-полей без CKEditor)
            if name in SCROLL_FIELDS:
                classes.append("gd-review-scroll")

            # аккуратно добавляем, если вдруг уже есть class
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()


class ReviewImageForm(forms.ModelForm):
    class Meta:
        model = ReviewImage
        fields = ("image",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " gd-field-control").strip()


ReviewImageFormSet = inlineformset_factory(
    parent_model=Review,
    model=ReviewImage,
    fields=("image", "caption", "order"),
    extra=3,
    can_delete=True
)


class ReviewCommentForm(forms.ModelForm):
    class Meta:
        model = ReviewComment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={
                "maxlength": 500,
                "rows": 4,
                "placeholder": "Оставьте комментарий…"
            })
        }