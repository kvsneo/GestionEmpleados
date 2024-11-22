import base64
import json
import os
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from logging_config import logger
from .Reconocimineto.IndexarBaseUsuarios import cargar_img_conocidad_directorio
from .admin import admin_required, admin_or_manager_required
from .forms import AdminCreationForm, ManagerCreationForm, EmployeeCreationForm, UserEditForm, ReassignManagerForm, \
    JustificanteForm, EmployeeProfileForm
from .forms import EmployeePasswordChangeForm
from .models import CustomUser, Justificante, JustificanteArchivo


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
            return redirect('dashboard')
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

            return redirect('dashboard')
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

            return redirect('dashboard')
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


@login_required
def index_photos(request):
    if request.method == 'POST':
        if cache.get('is_indexing'):
            return JsonResponse({'status': 'error', 'message': 'Indexing is already in progress.'})

        cache.set('is_indexing', True, timeout=None)  # Set the flag to indicate indexing is in progress
        try:
            messages = cargar_img_conocidad_directorio('UsuariosImagenes')
            return JsonResponse({'status': 'success', 'message': 'Indexing completed', 'messages': messages})
        finally:
            cache.delete('is_indexing')  # Clear the flag after indexing is done
    else:
        users = CustomUser.objects.all()
        return render(request, 'indexar_base.html', {'users': users})


@login_required
def dashboard(request):
    # Verificar los roles del usuario
    es_admin = request.user.is_admin()
    es_gerente = request.user.is_manager()
    es_empleado = request.user.is_employee()

    # Puedes crear variables adicionales si necesitas comprobar permisos específicos
    gestion_usuarios = es_admin  # Solo el admin puede gestionar usuarios
    reportes_globales = es_admin  # Solo el admin puede generar reportes globales
    gestion_empleados = es_gerente  # Solo el gerente puede gestionar empleados
    reportes_area = es_gerente  # Solo el gerente puede generar reportes de área
    registrar_asistencia = es_empleado  # Solo los empleados pueden registrar su asistencia
    consultar_estadisticas = es_empleado  # Solo los empleados pueden consultar estadísticas

    # Pasar los datos al contexto
    context = {
        'es_admin': es_admin,
        'es_gerente': es_gerente,
        'es_empleado': es_empleado,
        'gestion_usuarios': gestion_usuarios,
        'reportes_globales': reportes_globales,
        'gestion_empleados': gestion_empleados,
        'reportes_area': reportes_area,
        'registrar_asistencia': registrar_asistencia,
        'consultar_estadisticas': consultar_estadisticas,
    }

    return render(request, 'dashboard.html', context)


@login_required
def subir_justificante(request):
    if request.method == 'POST':
        form = JustificanteForm(request.POST, request.FILES)
        if form.is_valid():
            # Obtener los datos del formulario
            motivo = form.cleaned_data['motivo']
            fecha = form.cleaned_data['fecha']

            # Validar el campo 'motivo'
            if not motivo or motivo == "None":
                form.add_error('motivo', 'El motivo debe contener más detalles o no debe ser "None".')
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                return render(request, 'subir_justificante.html', {'form': form})

            # Obtener la fecha actual
            fecha_actual = timezone.now().astimezone(timezone.get_current_timezone()).date()

            # Calcular la fecha límite (hace 15 días desde la fecha actual)
            fecha_limite = fecha_actual - timedelta(days=15)

            # Validaciones de la fecha
            if fecha < fecha_limite:
                form.add_error('fecha', 'La fecha no puede ser anterior a los últimos 15 días.')
            if fecha > fecha_actual:
                form.add_error('fecha', 'La fecha no puede ser mayor a la fecha actual.')

            # Si hubo errores de validación, no se guarda y se vuelve a mostrar el formulario con los errores
            if form.errors:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                return render(request, 'subir_justificante.html', {'form': form})

            # Crear la instancia del justificante
            justificante = Justificante(
                motivo=motivo,
                fecha=fecha,
                empleado=request.user,  # Asigna al usuario actual como empleado
                usuario=request.user  # Asigna al usuario actual como quien sube
            )
            justificante.save()

            # Guardar archivos adjuntos si existen
            if request.FILES.get('imagen'):
                JustificanteArchivo.objects.create(justificante=justificante, archivo=request.FILES['imagen'],
                                                   tipo='imagen')
            if request.FILES.get('pdf'):
                JustificanteArchivo.objects.create(justificante=justificante, archivo=request.FILES['pdf'], tipo='pdf')
            if request.FILES.get('documento'):
                JustificanteArchivo.objects.create(justificante=justificante, archivo=request.FILES['documento'],
                                                   tipo='documento')

            # Mensaje de éxito
            messages.success(request, 'Justificante subido correctamente.')

            # Redirigir al dashboard después de mostrar el mensaje de éxito
            return render(request, 'subir_justificante.html', {'form': form})

        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')

    else:
        form = JustificanteForm()

    return render(request, 'subir_justificante.html', {'form': form})


@login_required
def lista_justificantes(request):
    # Filtrar justificantes según el rol del usuario
    if request.user.role == 'admin':
        # Los administradores pueden ver todos los justificantes
        justificantes = Justificante.objects.all()
    elif request.user.role == 'manager':
        # Los gerentes solo pueden ver los justificantes de los empleados que tienen asociados
        justificantes = Justificante.objects.filter(empleado__manager=request.user)
    elif request.user.role == 'employee':
        # Los empleados solo pueden ver sus propios justificantes
        justificantes = Justificante.objects.filter(empleado=request.user)
    else:
        messages.error(request, 'No tienes permiso para ver esta página.')
        return redirect('inicio')

    if request.method == 'POST':
        justificante_id = request.POST.get('justificante_id')

        # Manejo de eliminación
        if request.POST.get('eliminar_justificante') == 'true':
            try:
                # Los empleados solo pueden eliminar sus propios justificantes
                justificante = Justificante.objects.get(id=justificante_id, empleado=request.user)
                justificante.delete()
                messages.success(request, 'El justificante ha sido eliminado exitosamente.')
            except Justificante.DoesNotExist:
                messages.error(request, 'No tienes permiso para eliminar este justificante.')
            return redirect('lista_justificantes')

        # Manejo de actualización de estado (Aceptar o Rechazar)
        nuevo_estado = request.POST.get('nuevo_estado')
        if nuevo_estado in ['Aceptado', 'Rechazado']:
            try:
                justificante = Justificante.objects.get(id=justificante_id)
                # Solo gerentes o administradores pueden cambiar el estado
                if request.user.role in ['manager', 'admin']:
                    justificante.estado = nuevo_estado
                    justificante.save()
                    messages.success(request, f'El justificante ha sido {nuevo_estado.lower()} exitosamente.')
                else:
                    messages.error(request, 'No tienes permiso para realizar esta acción.')
            except Justificante.DoesNotExist:
                messages.error(request, 'El justificante no existe.')
            return redirect('lista_justificantes')

        # Manejo de edición por empleados
        nuevo_motivo = request.POST.get('nuevo_motivo')
        nuevo_archivo = request.FILES.get('nuevo_archivo')
        if nuevo_motivo or nuevo_archivo:
            try:
                justificante = Justificante.objects.get(id=justificante_id, empleado=request.user)
                if justificante.estado == 'Pendiente':
                    if nuevo_motivo:
                        justificante.motivo = nuevo_motivo
                    if nuevo_archivo:
                        JustificanteArchivo.objects.create(
                            justificante=justificante,
                            archivo=nuevo_archivo,
                            tipo='nuevo'  # Puedes adaptar el tipo si es necesario
                        )
                    justificante.save()
                    messages.success(request, 'El justificante ha sido actualizado.')
                else:
                    messages.error(request, 'Solo puedes editar justificantes en estado "Pendiente".')
            except Justificante.DoesNotExist:
                messages.error(request, 'No tienes permiso para editar este justificante.')
            return redirect('lista_justificantes')

    return render(request, 'lista_justificantes.html', {'justificantes': justificantes})


@login_required
def editar_justificante(request, justificante_id):
    justificante = get_object_or_404(Justificante, id=justificante_id)

    # Verifica si el usuario tiene el rol adecuado y si el estado es "Pendiente"
    if request.user != justificante.usuario and not request.user.is_manager():
        messages.error(request, 'No tienes permiso para editar este justificante.')
        return redirect('lista_justificantes')

    if justificante.estado != 'Pendiente':
        messages.error(request, 'No puedes editar un justificante que no está en estado "Pendiente".')
        return redirect('lista_justificantes')

    if request.method == 'POST':
        form = JustificanteForm(request.POST, request.FILES, instance=justificante)
        if form.is_valid():
            form.save()

            # Procesar archivos
            if 'imagen' in request.FILES:
                if justificante.archivos.filter(tipo='imagen').exists():
                    justificante.archivos.filter(tipo='imagen').delete()
                JustificanteArchivo.objects.create(
                    justificante=justificante,
                    archivo=request.FILES['imagen'],
                    tipo='imagen'
                )

            if 'pdf' in request.FILES:
                if justificante.archivos.filter(tipo='pdf').exists():
                    justificante.archivos.filter(tipo='pdf').delete()
                JustificanteArchivo.objects.create(
                    justificante=justificante,
                    archivo=request.FILES['pdf'],
                    tipo='pdf'
                )

            if 'documento' in request.FILES:
                if justificante.archivos.filter(tipo='documento').exists():
                    justificante.archivos.filter(tipo='documento').delete()
                JustificanteArchivo.objects.create(
                    justificante=justificante,
                    archivo=request.FILES['documento'],
                    tipo='documento'
                )

            # Agregar mensaje de éxito
            messages.success(request, 'Justificante actualizado exitosamente.')
            return redirect('editar_justificante',
                            justificante_id=justificante.id)  # Esto recarga la página para mostrar el mensaje

    else:
        form = JustificanteForm(instance=justificante)

    # Pasamos los archivos asociados al justificante
    archivos_imagen = justificante.archivos.filter(tipo='imagen')
    archivos_pdf = justificante.archivos.filter(tipo='pdf')
    archivos_documento = justificante.archivos.filter(tipo='documento')

    return render(request, 'editar_justificante.html', {
        'form': form,
        'archivos_imagen': archivos_imagen,
        'archivos_pdf': archivos_pdf,
        'archivos_documento': archivos_documento,
    })


@login_required
def edit_employee_profile(request):
    if request.method == 'POST':
        form = EmployeeProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('dashboard')
    else:
        form = EmployeeProfileForm(instance=request.user)

    return render(request, 'edit_employee_profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = EmployeePasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            old_password = form.cleaned_data.get('old_password')
            new_password1 = form.cleaned_data.get('new_password1')

            # Verify if the new password is the same as the old password
            if old_password == new_password1:
                messages.error(request, 'The new password cannot be the same as the old password.')
                return render(request, 'change_password.html', {'form': form})

            user = form.save()
            update_session_auth_hash(request, user)  # Keep the session active after changing the password

            # Send an email with the new password
            send_mail(
                'Your password has been changed',
                f'Hello {user.username},\n\nYour password has been successfully changed. Your new password is: {new_password1}\n\nBest regards,\nThe team',
                'your_email@example.com',
                [user.email],
                fail_silently=False,
            )

            messages.success(request, 'Your password has been successfully updated.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = EmployeePasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


from django.shortcuts import render, redirect
from .forms import ScheduleForm
from .models import EmployeeSchedule

def change_schedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            month = form.cleaned_data['month']
            schedule = form.cleaned_data['schedule']

            # Map the selected schedule to start and end times
            schedule_mapping = {
                '7am-3pm': ('07:00', '15:00'),
                '3pm-11pm': ('15:00', '23:00'),
                '11pm-7am': ('23:00', '07:00')
            }
            schedule_start, schedule_end = schedule_mapping[schedule]

            # Check if the schedule already exists for the employee and month
            employee_schedule, created = EmployeeSchedule.objects.update_or_create(
                employee=employee,
                month=month,
                defaults={'schedule_start': schedule_start, 'schedule_end': schedule_end}
            )
            return redirect('dashboard')
    else:
        form = ScheduleForm()

    return render(request, 'change_schedule.html', {'form': form})

