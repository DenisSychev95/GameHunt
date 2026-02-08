from django.contrib import admin
from .models import Profile, AdminMessages, UserMessages
from .forms import ProfileAdminForm
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from allauth.account.models import EmailAddress
# Во избежание многократного дублирования кода импортируем методы из utils
from .utils import mask_phone, mask_email, view_email
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()


class UserNickChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nick = ""
        try:
            nick = (obj.profile.nickname or "").strip()
        except Exception:
            pass

        # ✅ ник первым, username для различения
        if nick and nick != obj.username:
            return f"{nick} ({obj.username})"
        return obj.username


class AdminMessagesAdminForm(forms.ModelForm):
    user = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Отправитель',
    )

    class Meta:
        model = UserMessages
        fields = "__all__"


@admin.register(AdminMessages)
class AdminMessagesAdmin(admin.ModelAdmin):
    form = AdminMessagesAdminForm
    list_display = ("user_nick", "guest_name_display", "guest_email_display",
                    "created_at", "is_read_status", "topic")
    list_filter = ("is_read", "topic", "created_at")
    search_fields = ("message", "guest_name", "guest_email", "topic_custom",
                     "user__username", "user__profile__nickname")
    ordering = ("is_read", "-created_at")

    def user_nick(self, obj):
        # если отправитель зарегистрирован
        if obj.user_id:
            return obj.user.profile.nickname or obj.user.username
        return "не зарегистрирован"

    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"

    def guest_name_display(self, obj):
        return (obj.guest_name or "").strip() or "не указано"

    guest_name_display.short_description = "Имя (гость)"

    def guest_email_display(self, obj):
        return (obj.guest_email or "").strip() or "не указан"

    guest_email_display.short_description = "Email (гость)"

    def is_read_status(self, obj):
        if obj.is_read:
            return 'Да ✅'

        return 'Нет ⛔️'

    is_read_status.short_description = 'Прочитано'


class UserMessagesAdminForm(forms.ModelForm):
    user = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Получатель',
    )

    class Meta:
        model = UserMessages
        fields = "__all__"


@admin.register(UserMessages)
class UserMessagesAdmin(admin.ModelAdmin):
    form = UserMessagesAdminForm
    list_display = ("user_nick", "created_at",  "is_read_status",  "topic", "title", "sender")
    list_filter = ("is_read", "topic", "created_at")
    search_fields = ("title", "text", "user__username", "sender")
    ordering = ("is_read", "-created_at")

    def user_nick(self, obj):
        # ник у тебя всегда есть, но fallback на username оставим
        return obj.user.profile.nickname or obj.user.username

    user_nick.short_description = "Получатель(ник)"
    user_nick.admin_order_field = "user__username"

    def is_read_status(self, obj):
        if obj.is_read:
            return 'Да ✅️'

        return 'Нет ⛔'

    is_read_status.short_description = 'Прочитано'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    # Какую форму берем за основу
    form = ProfileAdminForm
    # что показываем в списке профилей
    list_display = ('user_nick', 'show_email', 'created', 'ban_status', 'site_status', 'age_group', 'masked_phone', )
    readonly_fields = ('created', 'last_seen',)
    # какие поля не видны и не редактируются из админки
    exclude = ('phone', 'first_name', 'last_name', 'email', 'bio', 'profile_image')

    def masked_phone(self, obj):
        return mask_phone(obj.phone)
    masked_phone.short_description = 'Телефон'

    def show_email(self, obj):
        return view_email(obj.email)
    show_email.short_description = 'Адрес электронной почты'

    def site_status(self, obj):
        return '🟢 online' if obj.is_online else '⚪️ offline'

    site_status.short_description = 'На сайте'

    def ban_status(self, obj):
        if obj.is_banned:
            return 'Да ⛔️'

        return 'Нет ✅'

    ban_status.short_description = 'Заблокирован'

    # # Не используем этот метод
    # def masked_email(self, obj):
    #     return mask_email(obj.email)
    # masked_email.short_description = 'email'

    # Определяем принадлежность к возрастной группу
    def age_group(self, obj):
        if obj.age is None:
            return 'не указан'
        return '16+' if obj.is_adult else '0-16'
    age_group.short_description = 'Возраст'

    def user_nick(self, obj):
        # ник у тебя всегда есть, но fallback на username оставим
        return obj.user.profile.nickname or obj.user.username

    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"


# Защищенная админка для User без прямого доступа к персональным данным
class SafeUserAdmin(BaseUserAdmin):

    # Что видит админ
    list_display = (
        'username',
        'user_nick',
        'show_email',
        'staff_status',
        'active_status',
    )

    def staff_status(self, obj):
        if obj.is_staff:
            return 'Да ✅'

        return 'Нет ⛔️'

    staff_status.short_description = 'Персонал сайта'

    def active_status(self, obj):
        if obj.is_active:
            return 'Да ✅'

        return 'Нет ⛔️'

    active_status.short_description = 'Пользователь активен'

    # Убираем возможность просматривать и редактировать
    exclude = ('first_name', 'last_name', 'show_email',)

    # КАКИЕ ПОЛЯ ПОКАЗЫВАЕМ В ФОРМЕ ИЗМЕНЕНИЯ
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    # Форма добавления нового пользователя в админке
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    # Оставляем поиск по username и email (поиск идёт по БД, не по отображению)
    search_fields = ('username', 'email', )

    def show_email(self, obj):
        return view_email(obj.email)
    show_email.short_description = 'Адрес электронной почты'

    # # Не используем этот метод
    # def masked_email(self, obj):
    #     return mask_email(obj.email)
    # masked_email.short_description = 'email'

    # Уберем маскированные поля имени, фамилии для Users
    """
    def masked_first_name(self, obj):
        # Видно первая буква и ***
        if not obj.first_name:
            return '-'
        name = obj.first_name.strip()
        if len(name) <= 2:
            return name[0] + '…'
        return name[:1] + '***'
    masked_first_name.short_description = 'Имя'

    def masked_last_name(self, obj):
        # Видно первая буква и ***
        if not obj.last_name:
            return '-'
        name = obj.last_name.strip()
        if len(name) <= 2:
            return name[0] + '…'
        return name[:1] + '***'
    masked_last_name.short_description = 'Фамилия'
    """
    def user_nick(self, obj):
        # ник у тебя всегда есть, но fallback на username оставим
        return obj.profile.nickname or obj.username

    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"

class SafeEmailAddressAdminForm(forms.ModelForm):
    user = UserNickChoiceField(
        queryset=User.objects.select_related("profile").all().order_by("profile__nickname", "username"),
        label='Пользователь',
    )

    class Meta:
        model = EmailAddress
        fields = "__all__"


class SafeEmailAddressAdmin(admin.ModelAdmin):
    form = SafeEmailAddressAdminForm
    list_display = ('user_nick', 'email', 'verified_status', 'primary_email_status',)
    search_fields = ('email',)
    list_display_links = ('user_nick',)

    def verified_status(self, obj):
        if obj.verified:
            return 'Да ✅'

        return 'Нет ⛔️'

    verified_status.short_description = 'Электронная почта подтверждена'

    def primary_email_status(self, obj):
        if obj.primary:
            return 'Да ✅'

        return 'Нет ⛔️'

    primary_email_status.short_description = 'Текущая почта является основной'

    def user_nick(self, obj):
        # ник у тебя всегда есть, но fallback на username оставим
        return obj.user.profile.nickname or obj.user.username

    user_nick.short_description = "Пользователь(ник)"
    user_nick.admin_order_field = "user__username"



    # # Не используем этот метод
    # def masked_email(self, obj):
    #     return mask_email(obj.email)
    # masked_email.short_description = 'email'


# Сначала отвязываем стандартного UserAdmin...
admin.site.unregister(User)
# Отвязать стандартный EmailAddress из админки
admin.site.unregister(EmailAddress)
# ...и регистрируем наш безопасный
admin.site.register(User, SafeUserAdmin)
# зарегистрировать безопасный SafeEmailAddressAdmin
admin.site.register(EmailAddress, SafeEmailAddressAdmin)
