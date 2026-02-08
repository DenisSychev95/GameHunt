from django.conf import settings
from django.db import models
from cryptography.fernet import InvalidToken, Fernet
from django.core.exceptions import ValidationError
import re
from django import forms
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from urllib.parse import quote
from django.urls import reverse
from urllib.parse import urlencode


def build_profile_content(request, owner_user, is_owner: bool):
    """
    Возвращает контекст для блока "Пользовательский контент" в профиле.

    content_tab = request.GET['content'] -> 'reviews' | 'walkthroughs'
    - Владелец профиля (is_owner=True): видит всё своё, получает edit/unpublish ссылки.
    - Посетитель (is_owner=False): видит только опубликованное, без действий.
    """

    # локальные импорты, чтобы избежать циклических импортов
    from reviews.models import Review
    from walkthroughs.models import Walkthrough

    # какая вкладка выбрана в профиле
    content_tab = request.GET.get("content", "reviews")
    if content_tab not in ("reviews", "walkthroughs"):
        content_tab = "reviews"

    # ссылка "вернуться туда, откуда пришли" (это сама страница профиля с querystring)
    next_url = request.get_full_path()
    next_qs = urlencode({"next": next_url})

    items = []

    if content_tab == "reviews":
        qs = (
            Review.objects
            .select_related("game")
            .filter(author=owner_user)
            .order_by("-updated_at", "-id")
        )

        # посетитель профиля видит только опубликованное
        if not is_owner:
            qs = qs.filter(is_published=True)

        for r in qs:
            edit_url = ""
            unpublish_url = ""
            if is_owner:
                edit_url = f"{reverse('review_edit', kwargs={'pk': r.pk})}?{next_qs}"
                unpublish_url = f"{reverse('review_delete', kwargs={'pk': r.pk})}?{next_qs}"

            items.append({
                "type": "review",
                "title": r.title,
                "detail_url": reverse("review_detail", kwargs={"pk": r.pk}),

                "game_title": r.game.title,
                "game_url": reverse("game_detail", kwargs={"slug": r.game.slug}),

                "updated_at": r.updated_at,
                "is_published": r.is_published,

                "edit_url": edit_url,
                "unpublish_url": unpublish_url,
            })

    else:  # walkthroughs
        qs = (
            Walkthrough.objects
            .select_related("game")
            .filter(author=owner_user)
            .order_by("-updated_at", "-id")
        )

        if not is_owner:
            qs = qs.filter(is_published=True)

        for w in qs:
            edit_url = ""
            unpublish_url = ""
            if is_owner:
                edit_url = f"{reverse('walkthrough_edit', kwargs={'slug': w.slug})}?{next_qs}"
                unpublish_url = f"{reverse('walkthrough_delete', kwargs={'slug': w.slug})}?{next_qs}"

            items.append({
                "type": "walkthrough",
                "title": w.title,
                "detail_url": reverse("walkthrough_detail", kwargs={"slug": w.slug}),

                "game_title": w.game.title,
                "game_url": reverse("game_detail", kwargs={"slug": w.game.slug}),

                "updated_at": w.updated_at,
                "is_published": w.is_published,

                "edit_url": edit_url,
                "unpublish_url": unpublish_url,
            })

    return {
        "content_tab": content_tab,
        "content_items": items,
        "is_owner": is_owner,
    }


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
                'Неверный формат телефона. Введите номер без +7(+8).'
            )
        return None

    return digits

