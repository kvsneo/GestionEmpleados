from datetime import time, timezone

from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.utils import timezone

from logging_config import logger
from .models import CustomUser, Justificante


class AdminCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        base_username = (self.cleaned_data['first_name'][:3] +
                         self.cleaned_data['last_name'][:3] +
                         self.cleaned_data['middle_name'][:3]).lower()
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
        if commit:
            user.save()
        return user


class ManagerCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        base_username = (self.cleaned_data['first_name'][:3] +
                         self.cleaned_data['last_name'][:3] +
                         self.cleaned_data['middle_name'][:3]).lower()
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
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
        base_username = (self.cleaned_data['first_name'][:3] +
                         self.cleaned_data['last_name'][:3] +
                         self.cleaned_data['middle_name'][:3]).lower()
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
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
from datetime import timedelta


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


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'middle_name', 'last_name', 'email']


class EmployeePasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class ScheduleForm(forms.Form):
    MONTH_CHOICES = [
        ('January', 'January'), ('February', 'February'), ('March', 'March'),
        ('April', 'April'), ('May', 'May'), ('June', 'June'),
        ('July', 'July'), ('August', 'August'), ('September', 'September'),
        ('October', 'October'), ('November', 'November'), ('December', 'December')
    ]

    SCHEDULE_CHOICES = [
        ('7am-3pm', '7am-3pm'),
        ('3pm-11pm', '3pm-11pm'),
        ('11pm-7am', '11pm-7am')
    ]

    employee = forms.ModelChoiceField(queryset=User.objects.none(), label='Empleado')
    month = forms.ChoiceField(choices=MONTH_CHOICES, label='Mes')
    schedule = forms.ChoiceField(choices=SCHEDULE_CHOICES, label='Horario')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ScheduleForm, self).__init__(*args, **kwargs)
        if user and user.is_manager():
            self.fields['employee'].queryset = CustomUser.objects.filter(manager=user)
        elif user and user.is_admin():
            self.fields['employee'].queryset = CustomUser.objects.filter(role='employee')


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

class PasswordResetVerifyForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)
    reset_code = forms.CharField(label="Reset Code", max_length=6)
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data