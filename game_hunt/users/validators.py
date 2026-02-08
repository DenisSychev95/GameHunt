from django.core.exceptions import ValidationError


class MinLengthValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"Придумайте другой пароль."
            )

    def get_help_text(self):
        return f"Минимум {self.min_length} символов."


class LettersAndDigitsValidator:

    def validate(self, password, user=None):
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise ValidationError(
                    "Придумайте другой пароль."
                )

    def get_help_text(self):
        return "Придумайте другой пароль."


class UpperAndLowerCaseValidator:
    def validate(self, password, user=None):
        if password.lower() == password or password.upper() == password:
            raise ValidationError(
                "Придумайте другой пароль."
            )

    def get_help_text(self):
        return "Добавьте заглавные и строчные буквы."