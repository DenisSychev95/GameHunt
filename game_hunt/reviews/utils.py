from datetime import date
from urllib.parse import urlparse, parse_qs


def can_view_adult(request) -> bool:
    """
    True если можно видеть контент 16+.
    Логика: гость / нет birth_date / возраст < 16 -> нельзя.
    staff/superuser -> можно всегда.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    profile = getattr(user, "profile", None)
    bd = getattr(profile, "birth_date", None)
    if not bd:
        return False

    today = date.today()
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return age >= 16


def _youtube_to_embed(url: str) -> str | None:
    if not url:
        return None
    try:
        u = urlparse(url)
    except Exception:
        return None

    host = (u.netloc or "").lower()

    if "youtube.com" in host and u.path.startswith("/embed/"):
        return url

    vid = None
    if "youtu.be" in host:
        vid = u.path.strip("/")
    elif "youtube.com" in host and u.path == "/watch":
        qs = parse_qs(u.query)
        vid = (qs.get("v") or [None])[0]

    return f"https://www.youtube.com/embed/{vid}" if vid else None