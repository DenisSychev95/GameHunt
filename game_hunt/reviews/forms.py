from django import forms
from .models import Review, ReviewImage, ReviewComment
from django.forms import inlineformset_factory
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .widgets import SimpleClearableFileInput


SCROLL_FIELDS = {'summary', 'conclusion'}


class AdminReviewCreateForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = (
            "game",
            "title",
            "summary",
            "cover_image",
            "text",
            "video_url",
            "pros",
            "cons",
            "conclusion",
            "rating",
        )
        widgets = {
            "text": CKEditorUploadingWidget(config_name="review"),
            "cover_image": SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            classes = ["gd-field-control"]
            if isinstance(field.widget, forms.Textarea):
                classes.append("gd-textarea")
            if name in SCROLL_FIELDS:
                classes.append("gd-scroll-field")  # или gd-review-scroll — как у тебя принято

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()

        self.fields["rating"].choices = [("", "Не выбрано"), *[(i, str(i)) for i in range(1, 11)]]


class ReviewAdminForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = (
            "title",
            "summary",
            'cover_image',
            "text",
            "video_url",
            "pros",
            "cons",
            "conclusion",
            "rating",
            "is_published",
        )
        widgets = {
            "text": CKEditorUploadingWidget(config_name="review"),
            'cover_image': SimpleClearableFileInput(),
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

        self.fields["rating"].choices = [
            ("", "Не выбрано"),
            *[(i, str(i)) for i in range(1, 11)]
        ]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = (
            "title",
            "summary",
            'cover_image',
            "text",
            "video_url",
            "pros",
            "cons",
            "conclusion",
            "rating",
        )
        widgets = {
            "text": CKEditorUploadingWidget(config_name="review"),
            'cover_image': SimpleClearableFileInput(),
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

        self.fields["rating"].choices = [
            ("", "Не выбрано"),
            *[(i, str(i)) for i in range(1, 11)]
        ]


class ReviewImageForm(forms.ModelForm):
    class Meta:
        model = ReviewImage
        fields = ("image", "caption", "order")
        widgets = {
            "image": SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " gd-field-control").strip()


ReviewImageFormSet = inlineformset_factory(
    parent_model=Review,
    model=ReviewImage,
    form=ReviewImageForm,
    fields=("image", "caption", "order"),
    extra=0,
    can_delete=True,

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