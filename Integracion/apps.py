from django.apps import AppConfig
from django.db.models.signals import post_migrate


class IntegracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Integracion'

    def ready(self):
        from .signals import crear_usuario_predeterminado
        post_migrate.connect(crear_usuario_predeterminado, sender=self)
