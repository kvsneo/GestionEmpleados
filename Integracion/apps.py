from django.apps import AppConfig
from django.db.models.signals import post_migrate


class IntegracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Integracion'

    def ready(self):
        from .signals import crear_usuario_predeterminado
        post_migrate.connect(crear_usuario_predeterminado, sender=self)
"""
Módulo de configuración de la aplicación Integracion.

Este módulo define la configuración de la aplicación `Integracion` y conecta la señal `post_migrate` 
con la función `crear_usuario_predeterminado` para crear un usuario predeterminado después de la migración.

Clases:
    IntegracionConfig: Configuración de la aplicación Integracion.

Funciones:
    ready: Método que se ejecuta cuando la aplicación está lista. Conecta la señal `post_migrate` 
           con la función `crear_usuario_predeterminado`.

Señales:
    post_migrate: Señal que se emite después de que se han aplicado las migraciones.

"""