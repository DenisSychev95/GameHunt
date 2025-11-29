from django.conf import settings
from django.db import models
from cryptography.fernet import InvalidToken
# Забираем из нашего utils методы шифрования и расшифровки
from .utils import encrypt_text, decrypt_text
from datetime import datetime, date


class EncryptedCharField(models.CharField):
    # EncryptedCharField- поле, перед записью в БД шифрует данные, когда считывает - расшифровывает,
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


# Шифруемое поле даты рождения
class EncryptedDateField(models.TextField):

    def from_db_value(self, value, expression, connection):
        # Расшифровывает дату из БД при чтении
        if value is None:
            return value

        try:
            decrypted = decrypt_text(value)
            return datetime.strptime(decrypted, "%d-%m-%Y").date()
        except Exception:
            return None  # или оставить value

    def to_python(self, value):
        # Преобразует значение к date , если приходит строка или дата.
        if value is None or isinstance(value, date):
            return value
        try:
            return datetime.strptime(value, "%d-%m-%Y").date()
        except Exception:
            return value

    def get_prep_value(self, value):
        # Перед сохранением в БД преобразуется в вид dd-mm-YYYY
        if value is None:
            return value

        if isinstance(value, date):
            value = value.strftime("%d-%m-%Y")

        return encrypt_text(value)
