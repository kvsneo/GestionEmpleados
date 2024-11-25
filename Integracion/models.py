from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('employee', 'Empleado'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'manager'},
        related_name='employees',
        help_text="Si el usuario es un empleado, asigna un gerente.",
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    reset_code = models.CharField(max_length=6, blank=True, null=True)  # Add this line

    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role == 'manager'

    def is_employee(self):
        return self.role == 'employee'


class Face(models.Model):
    name = models.CharField(max_length=255)
    encoding = models.BinaryField()
    photo_count = models.IntegerField()

    class Meta:
        db_table = 'faces'


class Justificante(models.Model):
    motivo = models.CharField(max_length=255)
    fecha = models.DateField()
    estado = models.CharField(max_length=50, default="Pendiente")
    empleado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='justificantes',
        limit_choices_to={'role': 'employee'}
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='justificantes_subidos'
    )

    def update_attendance_status(self):
        # Use the existing Attendance model to update the attendance status
        asis = asistencia.objects.filter(employee=self.empleado.username, date=self.fecha).first()
        if asis and asis.status == 'sn':
            asis.status = 'J'
            asis.save()


class asistencia(models.Model):
    employee = models.CharField(max_length=150)
    date = models.DateField()
    hora = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=2, default='sn')  # SN: Sin marcar, J: Justificado, A: Asistió, F: Falto

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"


class JustificanteArchivo(models.Model):
    justificante = models.ForeignKey(Justificante, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='justificantes/')
    tipo = models.CharField(max_length=50)  # Puede ser 'imagen', 'pdf' o 'documento'


class EmployeeSchedule(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedules')
    month = models.CharField(max_length=20)
    schedule_start = models.TimeField()
    schedule_end = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150)  # Add this field

    def __str__(self):
        return f"{self.employee.username} - {self.month} - {self.schedule_start} to {self.schedule_end}"


from django.contrib.auth.models import User


class MatchInfo(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    match_time = models.TimeField()
    class Meta:
        db_table = 'match_info'