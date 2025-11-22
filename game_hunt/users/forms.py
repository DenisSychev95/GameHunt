from allauth.account.forms import SignupForm
from django import forms
from django.forms.widgets import SelectDateWidget
from datetime import date
import re


class GameHuntSignupForm(SignupForm):
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

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone

        digits = re.sub(r'\D', '', phone)

        if len(digits) == 11 and digits.startswith('8'):
            digits = '7' + digits[1:]

        if len(digits) == 10 and digits.startswith('9'):
            digits = '7' + digits

        if len(digits) == 11 and digits.startswith('7'):
            return digits   # храним в БД как 79991234567

        raise forms.ValidationError('Неверный формат телефона. Ожидается номер вида 79991234567.')

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

        if not profile.nickname:
            profile.nickname = user.first_name or user.username

        profile.save()

        return user
