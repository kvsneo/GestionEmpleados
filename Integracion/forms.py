from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class AdminCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2', 'email')


class ManagerCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2', 'email')


class EmployeeCreationForm(UserCreationForm):
    manager = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='manager'), required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2', 'email', 'manager')

    @classmethod
    def get_manager(cls, user):
        if user and user.role == 'manager':
            return user  # Si el usuario logueado es un manager, se devuelve ese usuario.
        return None  # Si no, se retorna None.

    def __init__(self, *args, **kwargs):
        # El formulario puede acceder al usuario desde el contexto de la vista
        user = kwargs.pop('user', None)  # Usamos kwargs.pop para obtener el usuario desde el contexto

        super().__init__(*args, **kwargs)

        # Si el usuario es un manager, lo asignamos como el manager predeterminado
        if user and user.role == 'manager':
            self.fields['manager'].initial = user
            self.fields['manager'].queryset = CustomUser.objects.filter(role='manager', id=user.id)
