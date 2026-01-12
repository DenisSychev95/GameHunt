from django.contrib import admin
from .models import Profile
from .forms import ProfileAdminForm
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from allauth.account.models import EmailAddress
# Во избежание многократного дублирования кода импортируем методы из utils
from .utils import mask_phone, mask_email, view_email


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Какую форму берем за основу
    form = ProfileAdminForm
    # что показываем в списке профилей
    list_display = ('user', 'show_email', 'created', 'ban_status', 'site_status', 'age_group', 'masked_phone', )
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


# Защищенная админка для User без прямого доступа к персональным данным
class SafeUserAdmin(BaseUserAdmin):

    # Что видит админ
    list_display = (
        'username',
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
    search_fields = ('username', 'email')

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


class SafeEmailAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'verified_status', 'primary_email_status',)
    search_fields = ('email',)

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
