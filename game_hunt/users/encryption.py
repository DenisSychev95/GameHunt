from django.conf import settings
from django.db import models
from cryptography.fernet import InvalidToken
# Забираем из нашего utils методы шифрования и расшифровки
from .utils import encrypt_text, decrypt_text


class EncryptedCharField(models.CharField):
    # EncryptedCharField- поле, перед записью в БД шифрует данные, когда считывает- расшифровывает,
    # защита от утечки данных.

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        return encrypt_text(value)

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        return decrypt_text(value)

    # Преобразование к "питоновскому" виду.
    # Django вызывает это и для данных из формы.
    def to_python(self, value):
        return super().to_python(value)
