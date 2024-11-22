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

class MatchInfo(models.Model):
    name = models.CharField(max_length=255)
    match_time = models.DateTimeField()

    class Meta:
        db_table = 'match_info'