from datetime import timedelta, timezone

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.utils import timezone

from logging_config import logger
from .models import CustomUser, Justificante

User = get_user_model()


class AdminCreationForm(UserCreationForm):
    """
    Formulario para la creación de usuarios administradores.

    Atributos:
        Meta (class): Metadatos del formulario.
    """

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email')

    def save(self, commit=True):
        """
        Guarda el usuario administrador con un nombre de usuario único.

        Args:
            commit (bool): Si se debe guardar el usuario en la base de datos.

        Returns:
            CustomUser: El usuario administrador creado.
        """
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
    """
    Formulario para la creación de usuarios gerentes.

    Atributos:
        Meta (class): Metadatos del formulario.
    """

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email')

    def save(self, commit=True):
        """
        Guarda el usuario gerente con un nombre de usuario único.

        Args:
            commit (bool): Si se debe guardar el usuario en la base de datos.

        Returns:
            CustomUser: El usuario gerente creado.
        """
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
    """
    Formulario para la creación de usuarios empleados.

    Atributos:
        manager (ModelChoiceField): Campo para seleccionar el gerente del empleado.
        Meta (class): Metadatos del formulario.
    """
    manager = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='manager'), required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'password1', 'password2', 'email', 'manager')

    def save(self, commit=True):
        """
        Guarda el usuario empleado con un nombre de usuario único.

        Args:
            commit (bool): Si se debe guardar el usuario en la base de datos.

        Returns:
            CustomUser: El usuario empleado creado.
        """
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
        """
        Inicializa el formulario con el usuario actual.

        Args:
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave.
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.role == 'manager':
            self.fields['manager'].initial = user
            self.fields['manager'].queryset = CustomUser.objects.filter(role='manager', id=user.id)


class UserEditForm(forms.ModelForm):
    """
    Formulario para editar los detalles del usuario.

    Atributos:
        Meta (class): Metadatos del formulario.
    """

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'manager']

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario.

        Args:
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave.
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.role == 'manager':
            self.fields['role'].disabled = True
            self.fields['manager'].disabled = True


class ReassignManagerForm(forms.Form):
    """
    Formulario para reasignar un gerente a un usuario.

    Atributos:
        new_manager (ModelChoiceField): Campo para seleccionar el nuevo gerente.
    """
    new_manager = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='manager'), required=True)

    def save(self, user):
        """
        Guarda la nueva asignación de gerente.

        Args:
            user (CustomUser): El usuario que está siendo reasignado.

        Returns:
            CustomUser: El nuevo gerente.
        """
        new_manager = self.cleaned_data['new_manager']
        logger.info(f"Manager reassigned: {user.username} to {new_manager.username}")
        return new_manager


class JustificanteForm(forms.ModelForm):
    """
    Formulario para enviar justificantes (documentos de prueba).

    Atributos:
        imagen (FileField): Campo para archivos de imagen.
        pdf (FileField): Campo para archivos PDF.
        documento (FileField): Campo para archivos de documento.
        Meta (class): Metadatos del formulario.
    """

    class Meta:
        model = Justificante
        fields = ['fecha', 'motivo', 'imagen', 'pdf', 'documento']
        widgets = {'fecha': forms.DateInput(attrs={'type': 'date'})}

    imagen = forms.FileField(required=False)
    pdf = forms.FileField(required=False)
    documento = forms.FileField(required=False)

    def clean_imagen(self):
        """
        Valida el archivo de imagen.

        Returns:
            File: El archivo de imagen validado.

        Raises:
            forms.ValidationError: Si el archivo no es una imagen válida o excede los límites de tamaño.
        """
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            valid_extensions = ['jpg', 'jpeg', 'png']
            file_extension = imagen.name.split('.')[-1].lower()
            if file_extension not in valid_extensions:
                raise forms.ValidationError("Solo se permiten imágenes en formato JPG, JPEG o PNG.")
            if imagen.size > 2 * 1024 * 1024:
                raise forms.ValidationError("La imagen no debe exceder los 2 MB.")
        return imagen

    def clean_pdf(self):
        """
        Valida el archivo PDF.

        Returns:
            File: El archivo PDF validado.

        Raises:
            forms.ValidationError: Si el archivo no es un PDF válido o excede los límites de tamaño.
        """
        pdf = self.cleaned_data.get('pdf')
        if pdf:
            if not pdf.name.endswith('.pdf'):
                raise forms.ValidationError("Solo se permiten archivos en formato PDF.")
            if pdf.size > 5 * 1024 * 1024:
                raise forms.ValidationError("El archivo PDF no debe exceder los 5 MB.")
        return pdf

    def clean_documento(self):
        """
        Valida el archivo de documento.

        Returns:
            File: El archivo de documento validado.

        Raises:
            forms.ValidationError: Si el archivo no es un documento válido o excede los límites de tamaño.
        """
        documento = self.cleaned_data.get('documento')
        if documento:
            valid_extensions = ['doc', 'docx']
            file_extension = documento.name.split('.')[-1].lower()
            if file_extension not in valid_extensions:
                raise forms.ValidationError("Solo se permiten documentos en formato DOC o DOCX.")
            if documento.size > 5 * 1024 * 1024:
                raise forms.ValidationError("El documento no debe exceder los 5 MB.")
        return documento

    def clean_fecha(self):
        """
        Valida la fecha.

        Returns:
            date: La fecha validada.

        Raises:
            forms.ValidationError: Si la fecha no está dentro del rango permitido.
        """
        fecha = self.cleaned_data['fecha']
        fecha_actual = timezone.now().date()
        if fecha > fecha_actual:
            raise forms.ValidationError('La fecha no puede ser mayor a la fecha actual.')
        fecha_limite = fecha_actual - timedelta(days=15)
        if fecha < fecha_limite:
            raise forms.ValidationError('La fecha no puede ser anterior a los últimos 15 días.')
        return fecha

class EmployeeProfileForm(forms.ModelForm):
    """
    Formulario para editar los detalles del perfil del empleado.

    Atributos:
        Meta (class): Metadatos del formulario.
    """

    class Meta:
        model = CustomUser
        fields = ['first_name', 'middle_name', 'last_name', 'email']


class EmployeePasswordChangeForm(PasswordChangeForm):
    """
    Formulario para cambiar la contraseña del empleado.

    Atributos:
        old_password (CharField): Campo para la contraseña anterior.
        new_password1 (CharField): Campo para la nueva contraseña.
        new_password2 (CharField): Campo para confirmar la nueva contraseña.
    """
    old_password = forms.CharField(
        label='Clave anterior',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='Nueva Clave',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label='Confirmar Clave',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class ScheduleForm(forms.Form):
    """
    Formulario para programar los turnos de los empleados.

    Atributos:
        MONTH_CHOICES (list): Lista de opciones de meses.
        SCHEDULE_CHOICES (list): Lista de opciones de horarios.
        employee (ModelChoiceField): Campo para seleccionar al empleado.
        month (ChoiceField): Campo para seleccionar el mes.
        schedule (ChoiceField): Campo para seleccionar el horario.
    """
    MONTH_CHOICES = [
        ('0000-01-00', 'January'), ('0000-02-00', 'February'), ('0000-03-00', 'March'),
        ('0000-04-00', 'April'), ('0000-05-00', 'May'), ('0000-06-00', 'June'),
        ('0000-07-00', 'July'), ('0000-08-00', 'August'), ('0000-09-00', 'September'),
        ('0000-10-00', 'October'), ('0000-11-00', 'November'), ('0000-12-00', 'December')
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
        """
        Inicializa el formulario.

        Args:
            *args: Argumentos posicionales.
            **kwargs: Argumentos de palabra clave.
        """
        user = kwargs.pop('user', None)
        super(ScheduleForm, self).__init__(*args, **kwargs)
        if user and user.is_manager():
            self.fields['employee'].queryset = CustomUser.objects.filter(manager=user)
        elif user and user.is_admin():
            self.fields['employee'].queryset = CustomUser.objects.filter(role='employee')


class PasswordResetRequestForm(forms.Form):
    """
    Formulario para solicitar un restablecimiento de contraseña.

    Atributos:
        email (EmailField): Campo para la dirección de correo electrónico.
    """
    email = forms.EmailField(label="Email", max_length=254)


class PasswordResetVerifyForm(forms.Form):
    """
    Formulario para verificar una solicitud de restablecimiento de contraseña.

    Atributos:
        email (EmailField): Campo para la dirección de correo electrónico.
        reset_code (CharField): Campo para el código de restablecimiento.
        new_password1 (CharField): Campo para la nueva contraseña.
        new_password2 (CharField): Campo para confirmar la nueva contraseña.
    """
    email = forms.EmailField(label="Email", max_length=254)
    reset_code = forms.CharField(label="Reset Code", max_length=6)
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput)

    def clean(self):
        """
        Valida los datos del formulario.

        Returns:
            dict: Los datos validados.

        Raises:
            forms.ValidationError: Si las contraseñas no coinciden.
        """
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data