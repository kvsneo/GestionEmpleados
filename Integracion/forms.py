from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser
from logging_config import logger



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


class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'manager']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.role == 'manager':
            self.fields['role'].disabled = True
            self.fields['manager'].disabled = True


class ReassignManagerForm(forms.Form):
    new_manager = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='manager'), required=True)

    def save(self, user):
        new_manager = self.cleaned_data['new_manager']
        logger.info(f"Manager reassigned: {user.username} to {new_manager.username}")
        return new_manager