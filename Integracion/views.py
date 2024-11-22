from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from logging_config import logger
from .admin import admin_required, admin_or_manager_required
from .forms import AdminCreationForm, ManagerCreationForm, EmployeeCreationForm, UserEditForm, ReassignManagerForm
from .models import CustomUser


# Create your views here.
@require_http_methods(["POST", "GET"])
@login_required
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
    logger.warning(f"Unauthorized access attempt by {request.user.username} for user {username} with role {role}")
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
            logger.info(f"Admin created: {user.username} by {request.user.username}")
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
            logger.info(f"Manager created: {user.username} by {request.user.username}")

            # Enviar correo electrónico
            send_mail(
                'Cuenta de Gerente Creada',
                f'Su nombre de usuario es {user.username} y su contraseña es {form.cleaned_data["password1"]}',
                'your_email@example.com',
                [user.email],
                fail_silently=False,
            )

            return redirect('admin_dashboard')
    else:
        form = ManagerCreationForm()
    return render(request, 'create_manager.html', {'form': form})


@login_required
@admin_or_manager_required
def create_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'employee'
            user.save()
            logger.info(f"Employee created: {user.username} by {request.user.username}")

            # Enviar correo electrónico
            send_mail(
                'Cuenta de Empleado Creada',
                f'Su nombre de usuario es {user.username} y su contraseña es {form.cleaned_data["password1"]}',
                'your_email@example.com',
                [user.email],
                fail_silently=False,
            )

            return redirect('admin_dashboard')
    else:
        form = EmployeeCreationForm(user=request.user)
        # Si el usuario es un manager, desactivamos el campo 'manager'
        if request.user.role == 'manager':
            form.fields['manager'].widget.attrs['disabled'] = 'disabled'
            form.fields['manager'].widget.attrs['style'] = 'background-color: #f0f0f0; color: #888;'
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


@login_required
@admin_or_manager_required
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            form.save()
            logger.info(f"User edited: {user.username} by {request.user.username}")
            return redirect('list_users')
    else:
        form = UserEditForm(instance=user, user=request.user)
    return render(request, 'edit_user.html', {'form': form})


@login_required
@admin_or_manager_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        if user.role == 'admin':
            # Verificar si es el último administrador
            admin_count = CustomUser.objects.filter(role='admin').count()
            if admin_count <= 1:
                messages.error(request, 'No puedes eliminar el último administrador.')
                logger.warning(f"Attempt to delete the last admin: {user.username} by {request.user.username}")
                return redirect('list_users')

        if user.role == 'manager':
            form = ReassignManagerForm(request.POST)
            if form.is_valid():
                new_manager = form.cleaned_data['new_manager']
                employees = user.employees.all()
                for employee in employees:
                    employee.manager = new_manager
                    employee.save()
                user.delete()
                logger.info(f"Manager deleted: {user.username} by {request.user.username}")
                return redirect('list_users')
        else:
            user.delete()
            logger.info(f"User deleted: {user.username} by {request.user.username}")
            return redirect('list_users')
    else:
        form = ReassignManagerForm()

    return render(request, 'confirm_delete.html', {'user': user, 'form': form})


def capturarimagenes(request):
    return render(request, 'capturarImagenes.html')

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import base64
import os
from django.conf import settings

@csrf_exempt
def save_image(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        image_data = data['image'].split(',')[1]
        capture_count = data['captureCount']
        image_binary = base64.b64decode(image_data)

        # Define the base path and user directory
        base_path = os.path.join(settings.MEDIA_ROOT, 'UsuariosImagenes', request.user.username)
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        # Find the next available filename
        image_path = os.path.join(base_path, f'image_{capture_count}.png')
        while os.path.exists(image_path):
            capture_count += 1
            image_path = os.path.join(base_path, f'image_{capture_count}.png')

        with open(image_path, 'wb') as f:
            f.write(image_binary)

        return JsonResponse({'status': 'success', 'image_path': image_path})
    return JsonResponse({'status': 'error'}, status=400)