from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, post_migrate
from django.contrib.auth.models import Group
from django.dispatch import receiver
from .models import Profile


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
    # Для начала удалим наш user из всех групп
    user.groups.remove(nonadults_group, adults_group, banned_group)

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
            # Если возраст профиля >=18 добавляем user в группу совершеннолетних
            if instance.is_adult:
                user.groups.add(adults_group)
            else:
                # Если возраст 18< добавляем user в группу несовершеннолетних
                user.groups.add(nonadults_group)
    # Сохраняем user
    user.save()
