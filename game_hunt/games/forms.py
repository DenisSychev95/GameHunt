from django import forms
from .models import GameComment
from .models import Game, GameImage
from datetime import date
from django.forms import inlineformset_factory
from slugify import slugify
from reviews.widgets import SimpleClearableFileInput


class GameAdminPanelForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = (
            "title",
            "description",
            'release_date',
            "cover_image",
            "genres",
            "platforms",
            'developer',
            'publisher',
            "trailer_url",
            "is_adult_only",
        )
        widgets = {
            'release_date': forms.SelectDateWidget(
                years=range(date.today().year, date.today().year - 40, -1)
            ),
            'cover_image': SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # slug в форме не показываем
        if "slug" in self.fields:
            self.fields.pop("slug")

        # вычисляемые поля убираем (если вдруг попали)
        for name in ("avg_rating", "rating_avg", "liked_percent", "likes_percent", "likes_count", "views_count"):
            if name in self.fields:
                self.fields.pop(name)

        # классы как у остальных форм
        for f in self.fields.values():
            cls = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (cls + " gd-field-control").strip()
        # общий класс "со скроллом" для этих трёх полей
        for name in ("description", "genres", "platforms"):
            if name in self.fields:
                cls = self.fields[name].widget.attrs.get("class", "")
                self.fields[name].widget.attrs["class"] = (cls + " gd-scroll-field").strip()

            # точечно для description — запрет растягивания + скролл
        if "description" in self.fields:
            self.fields["description"].widget.attrs.update({
                "rows": 6,  # опционально: фиксируем высоту
                "style": "resize:none; overflow-y:auto;",
                })

    def save(self, commit=True):
        obj = super().save(commit=False)

        # ✅ python-slugify нормально транслитерирует кириллицу
        base = slugify(obj.title) or "game"
        slug = base

        qs = Game.objects.all()
        if obj.pk:
            qs = qs.exclude(pk=obj.pk)

        i = 2
        while qs.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1

        obj.slug = slug

        if commit:
            obj.save()
            self.save_m2m()

        return obj


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


class GameImageForm(forms.ModelForm):
    class Meta:
        model = GameImage
        fields = ("image", "caption", "position")
        widgets = {
            "image": SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " gd-field-control").strip()


# Вот он — inline formset: “несколько ReviewImage для одного Review”
GameImageFormSet = inlineformset_factory(
    parent_model=Game,
    model=GameImage,
    form=GameImageForm,
    fields=("image", "caption", "position"),
    extra=0,         # покажем 0 пустых формы под новые картинки
    can_delete=True  # можно удалить существующую картинку
)