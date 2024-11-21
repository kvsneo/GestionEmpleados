from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser
from logging_config import logger



class AdminCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email')


class ManagerCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = (self.cleaned_data['first_name'][:3] +
                         self.cleaned_data['last_name'][:3] +
                         self.cleaned_data['middle_name'][:3]).lower()
        if commit:
            user.save()
        return user


class EmployeeCreationForm(UserCreationForm):
    manager = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='manager'), required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email', 'manager')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = (self.cleaned_data['first_name'][:3] +
                         self.cleaned_data['last_name'][:3] +
                         self.cleaned_data['middle_name'][:3]).lower()
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
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