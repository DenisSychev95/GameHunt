from django.conf import settings
from django.db import models
from cryptography.fernet import InvalidToken, Fernet
from django.core.exceptions import ValidationError
import re


def encrypt_text(plain):
    # Шифрует приходящее значение в base64-токен.
    if plain is None or plain == '':
        return plain
    data = plain.encode('utf-8')
    token = settings.FERNET.encrypt(data)
    return token.decode('utf-8')


def decrypt_text(token):
    # Расшифровывает base64-токен.
    if token is None or token == '':
        return token
    try:
        data = settings.FERNET.decrypt(token.encode('utf-8'))
        return data.decode('utf-8')
    except InvalidToken:
        return token


# Показываем маску телефона вместо полного значения(в админке).
def mask_phone(number):
    if not number:
        return 'не указан'
    phone = str(number).strip()
    # телефон хранится в виде '79991234567'
    # в админке видно 7999*******
    return phone[:4] + '*' * 7


# Показываем маску email вместо полного значения(в админке).
def mask_email(email):
    # Mail видно в формате ***@mail.ru
    if not email:
        return 'не указан'
    email = email.strip()
    if '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    return f'***@{domain}'


# Используем этот метод для замены "-" в админке на произвольный текст
def view_email(email):
    if not email:
        return 'не указан'
    return email


# Метод преобразует телефон к виду 79999871234
def normalize_phone(phone_number, raise_on_error=True):
    # Оставляет только цифры, все форматы сводит к 79999871234, проверяет длину
    if not phone_number:
        return None
    # Фильтруем цифры
    digits = re.sub(r'\D', '', phone_number)

    # Ожидаемая длина 11 символов, приводим к единому формату 79999871234
    if len(digits) == 11 and digits[0] in ('7', '8'):
        digits = '7' + digits[1:]

    # Вызываем исключение если номер телефона меньше 11 символов или неподходящий формат
    if len(digits) != 11 or not digits.startswith('7'):
        if raise_on_error:
            raise ValidationError(
                'Неверный формат телефона. Ожидается номер вида 79991234567.'
            )
        return None

    return digits
