from allauth.account.forms import SignupForm, LoginForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import SelectDateWidget
from datetime import date
from .models import (Profile, AdminMessages, ADMIN_MESSAGE_CHOICES_GUEST, ADMIN_MESSAGE_CHOICES_AUTH,
                     USER_MESSAGE_CHOICES)
from . utils import normalize_phone
import re
from django.core.exceptions import ValidationError
from django.forms.forms import NON_FIELD_ERRORS
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import ResetPasswordForm
from allauth.account.forms import ResetPasswordKeyForm
from allauth.account.forms import ChangePasswordForm
from allauth.account.forms import AddEmailForm
from reviews.widgets import SimpleClearableFileInput
from django import forms
from django.contrib.auth import get_user_model
from .models import *


User = get_user_model()


class UserNickChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nick = ""
        try:
            nick = (obj.profile.nickname or "").strip()
        except Exception:
            pass
        return f"{nick} ({obj.username})" if nick and nick != obj.username else obj.username


class UserNickMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        nick = ""
        try:
            nick = (obj.profile.nickname or "").strip()
        except Exception:
            pass
        return f"{nick} ({obj.username})" if nick and nick != obj.username else obj.username


# ФОРМА ОТПРАВКИ СООБЩЕНИЯ АДМИНАМИ
class AdminSendUserMessageForm(forms.Form):
    send_to = forms.ChoiceField(
        label="Получатель",
        choices=[
            ("one", "Пользователь"),
            ("many", "Несколько пользователей"),
            ("all", "Все пользователи"),
        ],
        initial="one",
    )

    recipient = UserNickChoiceField(
        label="Пользователь",
        queryset=User.objects.select_related("profile").order_by("profile__nickname", "username"),
        required=False,
    )

    recipients = UserNickMultipleChoiceField(
        label="Пользователи",
        queryset=User.objects.select_related("profile").order_by("profile__nickname", "username"),
        required=False,
    )

    topic = forms.ChoiceField(label="Тема", choices=USER_MESSAGE_CHOICES)
    topic_custom = forms.CharField(label="Кратко", required=False)
    text = forms.CharField(label="Текст сообщения", widget=forms.Textarea(attrs={"rows": 7}))

    link = forms.URLField(label="Ссылка", required=False)

    image = forms.ImageField(
        label="Изображение",
        required=False,
        widget=SimpleClearableFileInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # классы для стиля
        for name, f in self.fields.items():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " gd-field-control").strip()

        # multiple-select чтобы было видно список
        self.fields["recipients"].widget.attrs["multiple"] = "multiple"
        self.fields["text"].widget.attrs["class"] += " gd-msg-text"

    def clean(self):
        cleaned = super().clean()

        send_to = cleaned.get("send_to")
        recipient = cleaned.get("recipient")
        recipients = cleaned.get("recipients")
        topic = cleaned.get("topic")
        topic_custom = (cleaned.get("topic_custom") or "").strip()

        if topic == "other" and not topic_custom:
            self.add_error("topic_custom", "Укажите тему.")

        if send_to == "one":
            if not recipient:
                self.add_error("recipient", "Выберите одного пользователя.")
        elif send_to == "many":
            if not recipients or len(recipients) < 2:
                self.add_error("recipients", "Выберите минимум двух пользователей.")
        elif send_to == "all":

            pass

        return cleaned


# ФОРМА ОТПРАВКИ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЕМ
class AuthUserToAdminForm(forms.ModelForm):
    topic = forms.ChoiceField(label="Тема", choices=ADMIN_MESSAGE_CHOICES_AUTH)

    class Meta:
        model = AdminMessages
        fields = ("topic", "topic_custom", "message", "image")
        labels = {
            "topic": "Тема",
            "topic_custom": "Коротко",
            "message": "Сообщение",
            "image": "Изображение",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
            'image': SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        existing = self.fields["message"].widget.attrs.get("class", "")
        self.fields["message"].widget.attrs["class"] = (existing + "gd-msg-text").strip()

        for f in self.fields.values():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " gd-field-control").strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("topic") == "other" and not (cleaned.get("topic_custom") or "").strip():
            self.add_error("topic_custom", "Укажите тему.")
        return cleaned


# ФОРМА ОТПРАВКИ СООБЩЕНИЯ ДЛЯ ГОСТЯ САЙТА
class GuestToAdminForm(forms.ModelForm):
    topic = forms.ChoiceField(label="Тема", choices=ADMIN_MESSAGE_CHOICES_GUEST)

    class Meta:
        model = AdminMessages
        fields = ("guest_name", "guest_email", "topic", "topic_custom", "message", "image")
        labels = {
            "guest_name": "Имя",
            "guest_email": "Email",
            "topic": "Тема",
            "topic_custom": "Коротко",
            "message": "Сообщение",
            "image": "Изображение",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
            'image': SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["guest_name"].required = True
        self.fields["guest_email"].required = True
        existing = self.fields["message"].widget.attrs.get("class", "")
        self.fields["message"].widget.attrs["class"] = (existing + "gd-msg-text").strip()

        for f in self.fields.values():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " gd-field-control").strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("topic") == "other" and not (cleaned.get("topic_custom") or "").strip():
            self.add_error("topic_custom", "Укажите свою тему.")
        return cleaned


class GameHuntAddEmailForm(AddEmailForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].label = "Дополнительный email"
        self.fields["email"].widget.attrs.update({
            "placeholder": "email",
            "class": "gd-field-control",
        })
        self.fields["email"].error_messages.update({
            "required": "Поле обязательно для заполнения",
            "invalid": "Введите корректный email",
        })


class GameHuntChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        f = self.fields

        # old password
        f["oldpassword"].label = "Старый пароль"
        f["oldpassword"].widget.attrs.update({
            "placeholder": "ваш пароль",
        })
        f["oldpassword"].error_messages.update({
            "required": "Поле обязательно для заполнения.",
        })

        # new password 1
        f["password1"].label = "Новый пароль"
        f["password1"].widget.attrs.update({
            "placeholder": "новый пароль",
        })
        f["password1"].error_messages.update({
            "required": "Поле обязательно для заполнения.",
        })

        # new password 2
        f["password2"].label = "Повторите пароль"
        f["password2"].widget.attrs.update({
            "placeholder": "повторите пароль",
        })
        f["password2"].error_messages.update({
            "required": "Поле обязательно для заполнения.",
        })


class GameHuntResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update({
            "placeholder": "введите пароль",
            "class": "gd-field-control",
        })
        self.fields["password2"].widget.attrs.update({
            "placeholder": "повторите пароль",
            "class": "gd-field-control",
        })


class GameHuntPasswordResetForm(ResetPasswordForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update({
            "placeholder": "email",
        })


# Кастомная форма регистрации
class GameHuntSignupForm(SignupForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'Логин',
            'email': 'Почта'
        }

    """ 
    first_name = forms.CharField(
        label='Имя',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ваше имя'}),
    )
    last_name = forms.CharField(
        label='Фамилия',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ваше фамилия'}),
    )
    """

    birth_date = forms.DateField(
        label='Дата рождения',
        required=False,
        widget=SelectDateWidget(
            years=range(date.today().year, date.today().year - 90, -1)
        ),

    )

    phone = forms.CharField(
        label='Телефон',
        required=False,
        help_text="Ввод номера телефона без +7 или +8"
    )

    # Переопределяем стандартные поля формы
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = date.today()
        self.fields["birth_date"].widget.attrs.update({
            "min": "1950-01-01",
            "max": today.strftime("%Y-%m-%d"),
            "class": "gd-field-control gd-wide",
        })



        f = self.fields

        # username / логин
        f['username'].label = 'Имя пользователя'
        f['username'].widget.attrs.update({
            'placeholder': 'логин'
        })

        # email
        f['email'].label = 'Электронная почта'
        f['email'].widget.attrs.update({
            'placeholder': 'email'
        })

        # пароль 1
        f['password1'].label = 'Пароль'
        f['password1'].help_text = 'Длина от 8 символов, обязательно наличие цифр и букв разного регистра'
        f['password1'].widget.attrs.update({
            'placeholder': 'введите пароль'
        })

        # пароль 2
        f['password2'].label = 'Подтверждение пароля'
        f['password2'].help_text = ''  # убрали стандартное описание
        f['password2'].widget.attrs.update({
            'placeholder': 'повторите пароль'
        })

    def clean_birth_date(self):
        bd = self.cleaned_data.get('birth_date')
        if not bd:
            return bd  # дата рождения необязательная — просто пропускаем
        today = date.today()
        if bd:
            years = today.year - bd.year
            if (today.month, today.day) < (bd.month, bd.day):
                years -= 1

            if not 7 < years < 90:
                raise ValidationError("Некорректная дата рождения")
        return bd

    # Используем подготовленный метод получения номера телефона
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        return normalize_phone(phone, raise_on_error=True)

    def save(self, request):
        # создаём User через allauth
        user = super().save(request)

        # приводим логин к нижнему регистру
        user.username = user.username.lower()

        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()

        # профиль уже создан сигналом
        profile = user.profile
        profile.birth_date = self.cleaned_data.get('birth_date')
        profile.phone = self.cleaned_data.get('phone')

        profile.email = user.email

        if not profile.nickname:
            profile.nickname = user.first_name or user.username

        profile.save()

        return user


# Кастомная форма авторизации
class GameHuntLoginForm(LoginForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['login'].widget.attrs.update({'placeholder': 'логин / почта / телефон'})
        self.fields['login'].error_messages.update({'required': 'Поле обязательно для заполнения'})
        self.fields['password'].widget.attrs.update({'placeholder': 'введите пароль'})
        self.fields['password'].error_messages.update({'required': 'Поле обязательно для заполнения'})

    # Расширяем форму LoginForm allauth для возможности авторизации по номеру телефона

    def clean_login(self):
        # базовая очистка allauth (обрежет пробелы и т.д.)
        login = super().clean_login()

        if not login:
            return login

        # Пробуем найти в поле логин номер телефона, но не выбрасываем исключение в случае если телефон не найден
        normalized = normalize_phone(login, raise_on_error=False)
        if normalized:
            # ИЩЕМ ПО РАССШИФРОВАННЫМ ТЕЛЕФОНАМ
            for profile in Profile.objects.exclude(phone__isnull=True):
                # profile.phone здесь уже РАСШИФРОВАНО EncryptedCharField'ом
                if profile.phone == normalized:
                    user = profile.user
                    # возвращаем логин этого пользователя
                    return user.get_username()

            # если никого не нашли по телефону — идём дальше как обычный логин

        # если логин не похож на телефон — остаётся стандартная логика allauth
        return login

    def clean(self):
        try:
            cleaned = super().clean()
        except ValidationError:
            # allauth часто валится сюда при неверных данных
            self._errors[NON_FIELD_ERRORS] = self.error_class([_("Неверный логин или пароль.")])
            return self.cleaned_data

        # если allauth всё же положил non-field errors без исключения
        if self.non_field_errors():
            msg = str(self.non_field_errors()[0])

            if ("Слишком много" in msg) or ("Повторите попытку позже" in msg):
                self._errors[NON_FIELD_ERRORS] = self.error_class([_("Слишком много попыток входа. Попробуйте позже.")])
            else:
                self._errors[NON_FIELD_ERRORS] = self.error_class([_("Неверный логин или пароль.")])

        return cleaned


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "nickname",
            "first_name",
            "last_name",
            "profile_image",
            "favorite_genres",
            "bio",
            "phone",
        ]
        labels = {
            "nickname": "Никнейм",
            "first_name": "Имя",
            "last_name": "Фамилия",
            "profile_image": "Картинка профиля",
            "favorite_genres": "Любимые жанры",
            "bio": "О себе",
            "phone": "Телефон",
        }
        widgets = {
            "profile_image": SimpleClearableFileInput(),  # как во 2-м фото
            "bio": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # жанры обязательны
        self.fields["favorite_genres"].required = True

        for name, field in self.fields.items():
            classes = ["gd-field-control"]

            if isinstance(field.widget, forms.Textarea):
                classes.append("gd-textarea")

            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + " ".join(classes)).strip()

        # телефон — placeholder и класс ширины
        self.fields["phone"].widget.attrs.update({
            "placeholder": "7(999)-999-99-99",
            "class": (self.fields["phone"].widget.attrs.get("class", "") + " gd-wide").strip(),
        })

        # file input: accept images (не обязательно, но удобно)
        self.fields["profile_image"].widget.attrs.update({
            "accept": "image/*",
        })

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone:
            return phone
        return normalize_phone(phone, raise_on_error=True)

    def clean_nickname(self):
        nick = (self.cleaned_data.get("nickname") or "").strip()
        if not nick:
            raise ValidationError("Никнейм обязателен.")
        return nick


class ProfileImageEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("profile_image",)
        labels = {"profile_image": "Картинка профиля"}
        widgets = {
            "profile_image": SimpleClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        f = self.fields["profile_image"]
        existing = f.widget.attrs.get("class", "")
        f.widget.attrs["class"] = (existing + " gd-field-control").strip()
        f.widget.attrs["accept"] = "image/*"


class ProfileAdminForm(forms.ModelForm):
    # Кастомная форма для админки, чтобы админ не видел дату рождения пользователя, мог менять дату рождения.
    # Банить профили

    birth_date = forms.DateField(
        label='Дата рождения',
        required=False,
        widget=SelectDateWidget(
            years=range(date.today().year, date.today().year - 90, -1)
        ),
    )

    class Meta:
        model = Profile
        # Определяем поля формы
        fields = ('birth_date', 'is_banned')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # Затираем полученное содержимое формы в админке
            self.initial['birth_date'] = None
            # Текст подсказки для поля формы с датой рождения
            self.fields['birth_date'].help_text = (
                'Текущая дата рождения не отображается. '
                'Укажите новую, только если нужно исправить.'
            )

    def save(self, commit=True):
        # Пока не сохраняем профиль
        profile = super().save(commit=False)

        # Получаем новое значение из поля формы
        new_bd = self.cleaned_data.get('birth_date')
        # Если поле оставили пустым — не меняем существующую дату
        if new_bd is None:
            profile.birth_date = self.instance.birth_date
        else:
            # Если указали новую — перезаписываем
            profile.birth_date = new_bd

        if commit:
            # Сохраняем профиль
            profile.save()
        return profile
