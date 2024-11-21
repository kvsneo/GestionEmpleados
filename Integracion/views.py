from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserCreationForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods

# Create your views here.
@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'is_admin': user.is_admin(),
        'is_manager': user.is_manager(),
        'is_employee': user.is_employee(),
        'managers': CustomUser.objects.filter(role='manager') if user.is_admin() else None,
        'create_admin_url': reverse('create_user', kwargs={'role': 'admin'}),
        'create_manager_url': reverse('create_user', kwargs={'role': 'manager'}),
        'create_employee_url': reverse('create_user', kwargs={'role': 'employee'}),
    }
    return render(request, 'dashboard.html', context)
@require_http_methods(["POST", "GET"])
def custom_logout(request):
    """Cerrar sesión con POST o redirigir con GET y cerrar Sesion"""
    if request.method == "POST":
        logout(request)
    else:
        logout(request)
    return redirect('login')







"""
@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'is_admin': user.is_admin(),
        'is_manager': user.is_manager(),
        'is_employee': user.is_employee(),
        'managers': CustomUser.objects.filter(role='manager') if user.is_admin() else None,
    }
    return render(request, 'dashboard.html', context)
"""
@login_required
def lista_usuarios(request):
    user = request.user
    if user.is_admin():
        # Administradores ven todos los usuarios
        administradores = CustomUser.objects.filter(role='admin')
        gerentes = CustomUser.objects.filter(role='manager')
        empleados = CustomUser.objects.filter(role='employee')
    elif user.is_manager():
        # Gerentes ven solo los empleados asignados
        administradores = None
        gerentes = None
        empleados = user.employees.all()
    else:
        # Empleados no tienen acceso
        return render(request, 'error.html', {'message': 'No tienes acceso a esta página.'})

    return render(request, 'lista_usuarios.html', {
        'administradores': administradores,
        'gerentes': gerentes,
        'empleados': empleados,
        'is_admin': user.is_admin(),
    })



"""""
@login_required
def create_user(request):
    if not request.user.is_admin() and not request.user.is_manager():
        return redirect('inicio')  # Redirige si no tiene permisos

    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        new_user = form.save(commit=False)
        # Si es un gerente, asignar automáticamente el gerente al empleado
        if request.user.is_manager() and new_user.role == 'employee':
            new_user.manager = request.user

        new_user.save()
        return redirect('lista_usuarios')  # Redirige después de crear el usuario

    return render(request, 'create_user.html', {'form': form})
"""
from django.urls import reverse

@login_required
def create_user(request, role=None):
    if not request.user.is_admin() and not request.user.is_manager():
        return redirect('inicio')  # Redirige si no tiene permisos

    form = UserCreationForm(request.POST or None)

    if role:
        form.fields['role'].initial = role

    if request.method == "POST" and form.is_valid():
        new_user = form.save(commit=False)
        # Si es un gerente, asignar automáticamente el gerente al empleado
        if request.user.is_manager() and new_user.role == 'employee':
            new_user.manager = request.user

        new_user.save()
        return redirect('lista_usuarios')  # Redirige después de crear el usuario

    return render(request, 'create_user.html', {'form': form, 'role': role})

