from django.contrib import admin
from .models import Profile
from .forms import ProfileAdminForm
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from allauth.account.models import EmailAddress
# Во избежание многократного дублирования кода импортируем методы из utils
from .utils import mask_phone, mask_email


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Какую форму берем за основу
    form = ProfileAdminForm
    # что показываем в списке профилей
    list_display = ('user', 'masked_phone', 'masked_email', 'created', 'is_online', 'is_banned', 'age_group',)
    readonly_fields = ('created', 'last_seen',)
    # какие поля не видны и не редактируются из админки
    exclude = ('phone', 'first_name', 'last_name', 'email', 'bio', 'profile_image')

    def masked_phone(self, obj):
        return mask_phone(obj.phone)
    masked_phone.short_description = 'Телефон'

    def masked_email(self, obj):
        return mask_email(obj.email)
    masked_email.short_description = 'email'

    # Определяем принадлежность к возрастной группу
    def age_group(self, obj):
        if obj.age is None:
            return '-'
        return '18+' if obj.is_adult else '0-17'
    age_group.short_description = 'Возрастная группа'

# Защищенная админка для User без прямого доступа к персональным данным
class SafeUserAdmin(BaseUserAdmin):

    # Что видит админ
    list_display = (
        'username',
        'masked_email',
        'is_staff',
        'is_active',
    )

    # Убираем возможность просматривать и редактировать
    exclude = ('first_name', 'last_name', 'email',)

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

    def masked_email(self, obj):
        return mask_email(obj.email)
    masked_email.short_description = 'email'

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
    list_display = ('user', 'masked_email', 'verified', 'primary',)
    search_fields = ('email',)

    def masked_email(self, obj):
        return mask_email(obj.email)
    masked_email.short_description = 'email'


# Сначала отвязываем стандартного UserAdmin...
admin.site.unregister(User)
# Отвязать стандартный EmailAddress из админки
admin.site.unregister(EmailAddress)
# ...и регистрируем наш безопасный
admin.site.register(User, SafeUserAdmin)
# зарегистрировать безопасный SafeEmailAddressAdmin
admin.site.register(EmailAddress, SafeEmailAddressAdmin)
