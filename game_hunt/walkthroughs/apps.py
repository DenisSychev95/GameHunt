from django.apps import AppConfig


class WalkthrougsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'walkthroughs'
    verbose_name = 'Прохождения'

    def ready(self):
        from . import signals
