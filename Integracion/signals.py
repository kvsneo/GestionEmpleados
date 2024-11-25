# signals.py
from django.contrib.auth import get_user_model

def crear_usuario_predeterminado(sender, **kwargs):
    User = get_user_model()
    # Crear usuario predeterminado con contraseña encriptada
    username = 'admin'
    email = 'admin@admin.com'
    password = 'admin'

    user, creado = User.objects.get_or_create(username=username,
                                              defaults={'email': email, 'is_staff': True, 'is_superuser': True, 'role': 'admin'})

    if creado:  # Si el usuario fue creado, configuramos la contraseña
        user.set_password(password)
        user.save()