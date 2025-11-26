from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # что показываем в списке профилей
    list_display = ('user', 'masked_phone', 'created', 'is_banned')
    readonly_fields = ('created',)
    # какие поля редактируются в форме из админки
    exclude = ('phone', )   # <-- телефон вообще не редактируем из админки

    def masked_phone(self, obj):
        """Показываем маску телефона вместо полного значения."""
        if not obj.phone:
            return '-'
        phone = str(obj.phone)
        # телефон хранится в виде '79991234567'
        # в админке видно 7999*******
        return phone[:4] + '*' * 7
    masked_phone.short_description = 'Телефон'
