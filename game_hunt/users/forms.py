from allauth.account.forms import SignupForm, LoginForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import SelectDateWidget
from datetime import date
from .models import Profile
from . utils import normalize_phone
import re


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
    )

    # Переопределяем стандартные поля формы
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        f = self.fields

        # username / логин
        f['username'].label = 'Логин'
        f['username'].widget.attrs.update({
            'placeholder': 'Придумайте логин'
        })

        # email
        f['email'].label = 'Адрес электронной почты'
        f['email'].widget.attrs.update({
            'placeholder': 'Укажите ваш email'
        })

        # пароль 1
        f['password1'].label = 'Пароль'
        f['password1'].help_text = ('Минимальная длина пароля 8 символов, пароль должен'
                                    ' содержать цифры и буквы разного регистра.')
        f['password1'].widget.attrs.update({
            'placeholder': 'Введите пароль'
        })

        # пароль 2
        f['password2'].label = 'Подтверждение пароля'
        f['password2'].help_text = ''  # убрали стандартное описание
        f['password2'].widget.attrs.update({
            'placeholder': 'Повторите пароля'
        })

    def clean_birth_date(self):
        bd = self.cleaned_data.get('birth_date')
        if not bd:
            return bd  # дата рождения необязательная — просто пропускаем

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


# Форма редактирования профиля
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['nickname', 'first_name', 'last_name', 'profile_image', 'bio', 'phone']
        labels = {
            'nickname': 'Никнейм',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone': 'Телефон',
            'profile_image': 'Картинка профиля',
            'bio': 'О себе',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    # Используем подготовленный метод получения номера телефона
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        return normalize_phone(phone, raise_on_error=True)


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
