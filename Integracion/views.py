from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .admin import admin_required, manager_required, admin_or_manager_required
from .forms import AdminCreationForm, ManagerCreationForm, EmployeeCreationForm
from .models import CustomUser


# Create your views here.
@require_http_methods(["POST", "GET"])
def custom_logout(request):
    """Cerrar sesión con POST o redirigir con GET y cerrar Sesion"""
    if request.method == "POST":
        logout(request)
    else:
        logout(request)
    return redirect('login')


@login_required
def error_view(request):
    username = request.GET.get('username', 'Unknown')
    role = request.GET.get('role', 'Unknown')
    message = f"Usuario: {username} con Rol: {role} no tiene acceso a esta página."
    return render(request, 'error.html', {'message': message})


@login_required
@admin_required
def create_admin(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'admin'
            user.save()
            return redirect('admin_dashboard')
    else:
        form = AdminCreationForm()
    return render(request, 'create_admin.html', {'form': form})


@login_required
@admin_required
def create_manager(request):
    if request.method == 'POST':
        form = ManagerCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'manager'
            user.save()
            return redirect('admin_dashboard')
    else:
        form = ManagerCreationForm()
    return render(request, 'create_manager.html', {'form': form})


@login_required
@manager_required
def create_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'employee'
            user.save()
            return redirect('admin_dashboard')
    else:
        form = EmployeeCreationForm(user=request.user)
        # Si el usuario es un manager, desactivamos el campo 'manager'
        if request.user.role == 'manager':
            form.fields['manager'].widget.attrs['disabled'] = 'disabled'  # Deshabilita el campo en el formulario
            form.fields['manager'].widget.attrs[
                'style'] = 'background-color: #f0f0f0; color: #888;'  # Estilo traslúcido

    return render(request, 'create_employee.html', {'form': form})


@login_required
@admin_or_manager_required
def list_users(request):
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

    return render(request, 'list_users.html', {
        'administradores': administradores,
        'gerentes': gerentes,
        'empleados': empleados,
        'is_admin': user.is_admin(),
    })
