from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, post_migrate
from django.contrib.auth.models import Group
from django.dispatch import receiver
from .models import Profile
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import pre_save
from django.urls import reverse


# Связываем функцию create_profile с сигналом создания экземпляра User- создается экземпляр Profile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, nickname=instance.username)


@receiver(post_migrate)
def create_groups(sender, **kwargs):
    # После миграции создаем новые группы, если они не существуют.
    # Ограничимся только миграциями приложения users.
    if sender.name != 'users':
        return

    groups = ['NonAdults', 'Adults', 'Banned']
    for group_name in groups:
        # Создаем нужные группы
        Group.objects.get_or_create(name=group_name)


@receiver(post_save, sender=Profile)
def update_user_group(sender, instance, **kwargs):
    # После редактирования и сохранения профиля:
    # is_banned=True => профиль добавлен в группу Banned, user.is_active=False
    # Сортировка по возрасту в группы NonAdults, Adults

    # Получили связанного с профилем user
    user = instance.user

    # Далее синтаксис кортежа т.к get_or_create() возвращает кортеж на 2 элемента
    # Получили 3 объекта Group для добавления/удаления нашего user
    nonadults_group, _ = Group.objects.get_or_create(name='NonAdults')
    adults_group, _ = Group.objects.get_or_create(name='Adults')
    banned_group, _ = Group.objects.get_or_create(name='Banned')
    simple_group, _ = Group.objects.get_or_create(name='SimpleUsers')
    # Для начала удалим наш user из всех групп
    user.groups.remove(nonadults_group, adults_group, banned_group, simple_group)

    if (not user.is_staff) and (not user.is_superuser):
        user.groups.add(simple_group)
    # Проверяем на бан профиля:
    if instance.is_banned:
        # Добавляем user в группу забаненых
        user.groups.add(banned_group)
        # Делаем неактивный user
        user.is_active = False
    else:
        # Удален флаг забаннего профиля и user снова активен
        user.is_active = True
        # Если не указан возраст профиля, по умолчанию добавляем в группу несовершеннолетних
        if instance.age is None:
            user.groups.add(nonadults_group)
        else:
            # Если возраст профиля >=16 добавляем user в группу совершеннолетних
            if instance.is_adult:
                user.groups.add(adults_group)
            else:
                # Если возраст 16< добавляем user в группу несовершеннолетних
                user.groups.add(nonadults_group)
    # Сохраняем user
    user.save()


@receiver(pre_save, sender=User)
def remember_prev_active(sender, instance, **kwargs):
    if not instance.pk:
        instance._was_active = True
        return
    prev = User.objects.filter(pk=instance.pk).values_list("is_active", flat=True).first()
    instance._was_active = bool(prev)


@receiver(post_save, sender=User)
def send_email_on_deactivate(sender, instance, **kwargs):
    was_active = getattr(instance, "_was_active", True)
    if (not was_active) or instance.is_active:
        return

    if not instance.email:
        return

    base = getattr(settings, "SITE_URL", "").rstrip("/")
    rules_url = base + reverse("rules")
    contact_url = base + reverse("contact_admin")

    subject = "GameHunt — аккаунт временно заблокирован"
    body = (
        "Здравствуйте!\n\n"
        "В связи с неоднократным нарушением правил пользования сайтом GameHunt "
        "ваш аккаунт на сайте временно заблокирован.\n\n"
        f"Правила: {rules_url}\n\n"
        "Вы можете обжаловать решение, отправив сообщение через форму обратной связи:\n"
        f"{contact_url}\n\n"
        "С уважением,\n"
        "Администрация GameHunt\n"
    )

    def _send():
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )

    transaction.on_commit(_send)