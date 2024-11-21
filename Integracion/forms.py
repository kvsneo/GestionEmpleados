# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import CustomUser

class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'role', 'manager')