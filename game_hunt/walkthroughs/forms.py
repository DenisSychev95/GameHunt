from django import forms
from django.forms import inlineformset_factory
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import Walkthrough, WalkthroughImage, WalkthroughComment
from reviews.widgets import SimpleClearableFileInput


SCROLL_FIELDS = {"summary"}


class AdminWalkthroughCreateForm(forms.ModelForm):
    class Meta:
        model = Walkthrough
        fields = (
            "game",
            "title",
            "cover_image",
            "summary",
            "text",
            "video_url",
        )
        widgets = {
            "text": CKEditorUploadingWidget(config_name="review"),
            "cover_image": SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " gd-field-control").strip()


class WalkthroughFormStaff(forms.ModelForm):
    class Meta:
        model = Walkthrough
        fields = (
            "title",
            "cover_image",
            "summary",
            "text",
            "video_url",
            "is_published",
        )
        widgets = {
            "text": CKEditorUploadingWidget(config_name="review"),
            "cover_image": SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # если у тебя есть общие классы — добавим (как в остальных формах)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " gd-field-control").strip()


class WalkthroughAdminForm(forms.ModelForm):
    class Meta:
        model = Walkthrough
        fields = (
            "title",
            "cover_image",
            "summary",
            "text",
            "video_url",
            "is_published",
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
                classes.append("gd-review-scroll")

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()


class WalkthroughFormUser(forms.ModelForm):
    class Meta:
        model = Walkthrough
        fields = (
            "title",
            "cover_image",
            "summary",
            "text",
            "video_url",
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
                classes.append("gd-review-scroll")

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()


class WalkthroughImageForm(forms.ModelForm):
    class Meta:
        model = WalkthroughImage
        fields = ("image", "caption", "order")
        widgets = {
            "image": SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields.values():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " gd-field-control").strip()


WalkthroughImageFormSet = inlineformset_factory(
    parent_model=Walkthrough,
    model=WalkthroughImage,
    form=WalkthroughImageForm,
    fields=("image", "caption", "order"),
    extra=0,
    can_delete=True,
)


class WalkthroughCommentForm(forms.ModelForm):
    class Meta:
        model = WalkthroughComment
        fields = ("text",)
        labels = {"text": "Комментарий"}
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        existing = self.fields["text"].widget.attrs.get("class", "")
        self.fields["text"].widget.attrs["class"] = (existing + " gd-field-control gd-textarea").strip()