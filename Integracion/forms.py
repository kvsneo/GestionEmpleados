from datetime import timedelta, timezone

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from logging_config import logger
from .models import CustomUser, Justificante


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


# varias evidencia, solo tres extensiones, verifica peso
class JustificanteForm(forms.ModelForm):
    class Meta:
        model = Justificante
        fields = ['fecha', 'motivo', 'imagen', 'pdf', 'documento']  # Incluye los campos de archivos aquí
        widgets = {'fecha': forms.DateInput(attrs={'type': 'date'}), }

    imagen = forms.FileField(required=False)  # Campo para imágenes
    pdf = forms.FileField(required=False)  # Campo para PDF
    documento = forms.FileField(required=False)  # Campo para documentos (DOC, DOCX)

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            valid_extensions = ['jpg', 'jpeg', 'png']
            file_extension = imagen.name.split('.')[-1].lower()
            if file_extension not in valid_extensions:
                raise forms.ValidationError("Solo se permiten imágenes en formato JPG, JPEG o PNG.")
            if imagen.size > 2 * 1024 * 1024:  # Límite de 2 MB por imagen
                raise forms.ValidationError("La imagen no debe exceder los 2 MB.")
        return imagen

    def clean_pdf(self):
        pdf = self.cleaned_data.get('pdf')
        if pdf:
            if not pdf.name.endswith('.pdf'):
                raise forms.ValidationError("Solo se permiten archivos en formato PDF.")
            if pdf.size > 5 * 1024 * 1024:  # Límite de 5 MB por PDF
                raise forms.ValidationError("El archivo PDF no debe exceder los 5 MB.")
        return pdf

    def clean_documento(self):
        documento = self.cleaned_data.get('documento')
        if documento:
            valid_extensions = ['doc', 'docx']
            file_extension = documento.name.split('.')[-1].lower()
            if file_extension not in valid_extensions:
                raise forms.ValidationError("Solo se permiten documentos en formato DOC o DOCX.")
            if documento.size > 5 * 1024 * 1024:  # Límite de 5 MB por documento
                raise forms.ValidationError("El documento no debe exceder los 5 MB.")
        return documento

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']

        # Obtener la fecha actual (sin hora, como objeto 'date')
        fecha_actual = timezone.now().date()  # Convierte la fecha y hora actual a 'date' (sin hora)

        # Verificar que la fecha no sea mayor a la fecha actual
        if fecha > fecha_actual:
            raise forms.ValidationError('La fecha no puede ser mayor a la fecha actual.')

        # Calcular la fecha límite (hace 15 días desde la fecha actual)
        fecha_limite = fecha_actual - timedelta(days=15)

        # Validar que la fecha no sea anterior a los últimos 15 días
        if fecha < fecha_limite:
            raise forms.ValidationError('La fecha no puede ser anterior a los últimos 15 días.')

        return fecha
