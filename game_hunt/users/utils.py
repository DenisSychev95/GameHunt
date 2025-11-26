from django.conf import settings
from django.db import models
from cryptography.fernet import InvalidToken


def encrypt_text(plain: str | None) -> str | None:
    # Шифрует приходящее значение в base64-токен.
    if plain is None or plain == '':
        return plain
    data = plain.encode('utf-8')
    token = settings.FERNET.encrypt(data)
    return token.decode('utf-8')


def decrypt_text(token: str | None) -> str | None:
    # Расшифровывает base64-токен.
    if token is None or token == '':
        return token
    try:
        data = settings.FERNET.decrypt(token.encode('utf-8'))
        return data.decode('utf-8')
    except InvalidToken:
        return token