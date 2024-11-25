from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from logging_config import logger
from .Reconocimineto.IndexarBaseUsuarios import cargar_img_conocidad_directorio
from .admin import admin_required, admin_or_manager_required
from .forms import AdminCreationForm, ManagerCreationForm, EmployeeCreationForm, UserEditForm, ReassignManagerForm, \
    JustificanteForm, EmployeeProfileForm, EmployeePasswordChangeForm, ScheduleForm
from .models import EmployeeSchedule, CustomUser, Justificante, JustificanteArchivo

BASE_DIR1 = 'UsuariosImagenes'


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


@login_required
def capturarimagenes(request):
    # Define the base path and user directory
    base_path = os.path.join(settings.MEDIA_ROOT, 'UsuariosImagenes', request.user.username)

    # Check the number of existing images
    if os.path.exists(base_path):
        existing_images = [f for f in os.listdir(base_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        remaining_images = 20 - len(existing_images)
        if remaining_images <= 0:
            return render(request, 'error.html', {'message': 'No se pueden registrar más de 20 imágenes.'})
        elif remaining_images < 5:
            return render(request, 'capturarImagenes.html', {'remaining_images': remaining_images})

    return render(request, 'capturarImagenes.html', {'remaining_images': 5})


@login_required
def get_remaining_images(request):
    # Define the base path and user directory
    base_path = os.path.join(settings.MEDIA_ROOT, 'UsuariosImagenes', request.user.username)

    # Check the number of existing images
    if os.path.exists(base_path):
        existing_images = [f for f in os.listdir(base_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        remaining_images = 20 - len(existing_images)
    else:
        remaining_images = 20

    return JsonResponse({'remaining_images': remaining_images})


@csrf_exempt
def save_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data['image'].split(',')[1]
            capture_count = data['captureCount']
            image_binary = base64.b64decode(image_data)

            # Define the base path and user directory
            base_path = os.path.join(settings.MEDIA_ROOT, 'UsuariosImagenes', request.user.username)
            if not os.path.exists(base_path):
                os.makedirs(base_path)

            # Check the number of existing images
            existing_images = [f for f in os.listdir(base_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            remaining_images = 20 - len(existing_images)
            if remaining_images <= 0:
                return JsonResponse({'status': 'error', 'message': 'No se pueden registrar más de 20 imágenes.'},
                                    status=400)
            elif capture_count > remaining_images:
                return JsonResponse(
                    {'status': 'error', 'message': f'Solo puedes capturar {remaining_images} imágenes más.'},
                    status=400)

            # Find the next available filename with leading zero for numbers less than 10
            image_path = os.path.join(base_path, f'image_{len(existing_images) + 1:02}.png')
            while os.path.exists(image_path):
                image_path = os.path.join(base_path,
                                          f'image_{len(existing_images) + len(os.listdir(base_path)) + 1:02}.png')

            with open(image_path, 'wb') as f:
                f.write(image_binary)

            return JsonResponse({'status': 'success', 'image_path': image_path})
        except Exception as e:
            logger.info(f"Error saving image: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error processing the image.'}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def index_photos(request):
    if request.method == 'POST':
        if cache.get('is_indexing'):
            logger.info('Indexing is already in progress.')
            logger.info('Indexing flag create.')
            return JsonResponse({'status': 'error', 'message': 'Indexing is already in progress.'})

        cache.set('is_indexing', True, timeout=None)  # Set the flag to indicate indexing is in progress
        try:
            messages = cargar_img_conocidad_directorio('UsuariosImagenes')
            return JsonResponse({'status': 'success', 'message': 'Indexing completed', 'messages': messages})
        except Exception as e:
            logger.info(f'Error during indexing: {e}')
            return JsonResponse({'status': 'error', 'message': 'An error occurred during indexing.'})
        finally:
            cache.delete('is_indexing')  # Clear the flag after indexing is done
            logger.info('Indexing flag cleared.')
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

        # Manejo de actualización de estado (Aceptar o Rechazar)
        nuevo_estado = request.POST.get('nuevo_estado')
        if nuevo_estado in ['Aceptado', 'Rechazado']:
            try:
                justificante = Justificante.objects.get(id=justificante_id)
                if request.user.role in ['manager', 'admin']:
                    justificante.estado = nuevo_estado
                    justificante.save()
                    if nuevo_estado == 'Aceptado':
                        justificante.update_attendance_status()
                    messages.success(request, f'El justificante ha sido {nuevo_estado.lower()} exitosamente.')
                else:
                    messages.error(request, 'No tienes permiso para realizar esta acción.')
            except Justificante.DoesNotExist:
                messages.error(request, 'El justificante no existe.')
            return redirect('lista_justificantes')

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


@login_required
def change_schedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST, user=request.user)
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
                defaults={
                    'schedule_start': schedule_start,
                    'schedule_end': schedule_end,
                    'username': employee.username  # Add the username here
                }
            )
            return redirect('dashboard')
    else:
        form = ScheduleForm(user=request.user)

    return render(request, 'change_schedule.html', {'form': form})


def buscar_imagenes(request):
    nombre_usuario = request.user.username
    ruta_usuario = os.path.join(settings.MEDIA_ROOT1, nombre_usuario)

    if os.path.exists(ruta_usuario) and os.path.isdir(ruta_usuario):
        imagenes = []
        for contador, archivo in enumerate(os.listdir(ruta_usuario), start=1):
            if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                imagenes.append(
                    {'numero': contador, 'nombre': archivo, 'ruta': f'{settings.MEDIA_URL1}{nombre_usuario}/{archivo}'})

        return render(request, 'mostrar_imagenes.html', {'imagenes': imagenes, 'nombre_usuario': nombre_usuario})
    else:
        return render(request, 'error.html', {'mensaje': 'El subdirectorio no existe o no contiene imágenes.'})


def eliminar_imagen(request, nombre_usuario, nombre_imagen):
    ruta_usuario = os.path.join(BASE_DIR1, nombre_usuario)
    imagenes = [archivo for archivo in os.listdir(ruta_usuario) if archivo.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if len(imagenes) <= 5:
        return render(request, 'error.html',
                      {'mensaje': 'No se puede eliminar la imagen. Debe tener al menos 5 imágenes.'})

    if request.method == 'POST':
        ruta_imagen = os.path.join(ruta_usuario, nombre_imagen)
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
            return HttpResponseRedirect(reverse('BuscarImagenes'))
    return render(request, 'error.html', {'mensaje': 'No se pudo eliminar la imagen.'})


'''''
def reconocimineto_usuarios(request):
    known_faces, known_names = obtener_rostros_conocidos()
    capturar_img_de_camara(known_faces, known_names)
    return HttpResponse("Ejecutando Reconocimiento.")
'''


@login_required
def reconocimiento_usuarios(request):
    return render(request, 'ReconocimientoUsuarios.html')


@login_required
def reportes(request):
    return render(request, "reportes.html")


@login_required
def reporte_justificantes(request):
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('dashboard')

    aceptados_count = 0
    rechazados_count = 0
    justificantes = Justificante.objects.exclude(estado='Pendiente')

    if request.user.role == 'manager':
        justificantes = justificantes.filter(empleado__manager=request.user)

    cuatrimestre = request.GET.get('cuatrimestre')
    anio = request.GET.get('anio')
    estado = request.GET.get('estado')

    if cuatrimestre and anio:
        try:
            cuatrimestre = int(cuatrimestre)
            anio = int(anio)
            current_year = datetime.now().year
            if anio < 2020 or anio > current_year:
                messages.error(request, f"El año debe estar entre 2020 y {current_year}.")
                return redirect('reporte_justificantes')

            if cuatrimestre == 1:
                meses = [1, 2, 3, 4]
            elif cuatrimestre == 2:
                meses = [5, 6, 7, 8]
            elif cuatrimestre == 3:
                meses = [9, 10, 11, 12]
            else:
                messages.error(request, "El cuatrimestre seleccionado no es válido.")
                return redirect('reporte_justificantes')

            justificantes = justificantes.filter(fecha__year=anio, fecha__month__in=meses)
        except ValueError:
            messages.error(request, "El cuatrimestre o el año seleccionado no son válidos.")
            return redirect('reporte_justificantes')
    elif request.GET:
        messages.warning(request, "Debes seleccionar un cuatrimestre y un año.")
        return redirect('reporte_justificantes')

    if estado:
        justificantes = justificantes.filter(estado=estado)

    if justificantes.exists():
        aceptados_count = justificantes.filter(estado='Aceptado').count()
        rechazados_count = justificantes.filter(estado='Rechazado').count()

    if not justificantes.exists() and request.GET:
        messages.info(request, "No hay justificantes registrados para los criterios seleccionados.")

    valid_years = list(range(2020, datetime.now().year + 1))

    context = {
        'justificantes': justificantes,
        'aceptados_count': aceptados_count,
        'rechazados_count': rechazados_count,
        'valid_years': valid_years,
        'cuatrimestre': cuatrimestre,
        'anio': anio,
        'estado': estado,
    }

    return render(request, 'reporte_justificantes.html', context)


def reporte_solicitudes(request):
    empleados = CustomUser.objects.none()
    if request.user.is_manager():
        empleados = CustomUser.objects.filter(manager=request.user)
    elif request.user.is_admin():
        empleados = CustomUser.objects.filter(role='employee')

    current_year = timezone.now().year
    years_range = range(2020, current_year + 1)

    report_data = None
    aceptados_count = 0
    rechazados_count = 0

    if request.method == 'POST':
        empleado_id = request.POST.get('employee')
        month = request.POST.get('month')
        year = request.POST.get('year')

        if not empleado_id or not month or not year:
            messages.error(request, "Por favor, selecciona un empleado, mes y año.")
        else:
            year = int(year)
            employee = CustomUser.objects.get(id=empleado_id)
            month_num = list(dict([
                ('January', 'Enero'), ('February', 'Febrero'), ('March', 'Marzo'),
                ('April', 'Abril'), ('May', 'Mayo'), ('June', 'Junio'),
                ('July', 'Julio'), ('August', 'Agosto'), ('September', 'Septiembre'),
                ('October', 'Octubre'), ('November', 'Noviembre'), ('December', 'Diciembre')
            ])).index(month) + 1

            start_date = timezone.datetime(year, month_num, 1)
            end_date = timezone.datetime(year, month_num + 1, 1) if month_num < 12 else timezone.datetime(year + 1, 1,
                                                                                                          1)

            report_data = Justificante.objects.filter(
                empleado=employee,
                fecha__gte=start_date,
                fecha__lt=end_date
            ).exclude(estado='Pendiente').select_related('empleado').values('motivo', 'fecha', 'estado',
                                                                            'empleado__first_name',
                                                                            'empleado__middle_name',
                                                                            'empleado__last_name')

            aceptados_count = report_data.filter(estado='Aceptado').count()
            rechazados_count = report_data.filter(estado='Rechazado').count()

            if not report_data:
                messages.warning(request,
                                 "No se encontraron justificantes para el empleado seleccionado en el mes y año indicados.")

    return render(request, 'reporte_solicitudes.html', {
        'empleados': empleados,
        'report_data': report_data,
        'years_range': years_range,
        'aceptados_count': aceptados_count,
        'rechazados_count': rechazados_count
    })


import cv2
import face_recognition
import mysql.connector
import numpy as np


def obtener_rostros_conocidos(db_name='basegestionempleados'):
    conn = mysql.connector.connect(host='localhost', user='root',  # Cambia a tu usuario de MySQL
                                   password='',  # Cambia a tu contraseña de MySQL
                                   database=db_name)
    c = conn.cursor()
    c.execute("SELECT name, encoding FROM faces")
    rows = c.fetchall()
    known_faces = []
    known_names = []
    for row in rows:
        name, encoding = row
        known_faces.append(np.frombuffer(encoding, dtype=np.float64))
        known_names.append(name)
    conn.close()
    return known_faces, known_names





def comparar_rostros(known_faces, known_names, captured_image_path):
    captured_image = face_recognition.load_image_file(captured_image_path)
    captured_image_encoding = face_recognition.face_encodings(captured_image)

    if not captured_image_encoding:
        raise ValueError("No se encontraron rostros en la imagen capturada.")

    for known_face, name in zip(known_faces, known_names):
        match = face_recognition.compare_faces([known_face], captured_image_encoding[0])
        if match[0]:
            # Insert match information into the database
            conn = mysql.connector.connect(host='localhost', user='root', password='', database='basegestionempleados')
            c = conn.cursor()
            match_time = datetime.now()  # Corrected this line
            c.execute("INSERT INTO match_info (name, match_time) VALUES (%s, %s)", (name, match_time))
            conn.commit()
            conn.close()
            return name
    return None


def capturar_img_de_camara(known_faces, known_names):
    video_capture = cv2.VideoCapture(1)
    while True:
        try:
            ret, frame = video_capture.read()
            cv2.imshow('Video', frame)

            # presiona 'q' para salir de la transmisión de la cámara
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # presiona la barra espaciadora para capturar la imagen
            if cv2.waitKey(1) & 0xFF == ord(' '):
                if ret:
                    cv2.imwrite('imagen_capturada.jpg', frame)
                    match_name = comparar_rostros(known_faces, known_names, 'imagen_capturada.jpg')
                    if match_name:
                        print(f"Rostro Coincide : {match_name}")
                    else:
                        print("No se encontró coincidencia.")
                else:
                    raise Exception("Error al capturar la imagen de la cámara")
        except Exception as e:
            print(f"Error: {e}")

    video_capture.release()
    cv2.destroyAllWindows()


import random
import string
from .forms import PasswordResetRequestForm, PasswordResetVerifyForm


def generate_reset_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.filter(email=email).first()
            if user:
                reset_code = generate_reset_code()
                user.reset_code = reset_code
                user.save()
                send_mail(
                    'Password Reset Code',
                    f'Your password reset code is: {reset_code}',
                    'your_email@example.com',
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'A reset code has been sent to your email.')
                return redirect('password_reset_verify')
            else:
                messages.error(request, 'No user found with this email.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'password_reset_request.html', {'form': form})


def password_reset_verify(request):
    if request.method == 'POST':
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            reset_code = form.cleaned_data['reset_code']
            new_password = form.cleaned_data['Nueva_Clave']
            user = CustomUser.objects.filter(email=email, reset_code=reset_code).first()
            if user:
                user.set_password(new_password)
                user.reset_code = ''
                user.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('login')
            else:
                messages.error(request, 'Invalid reset code or email.')
    else:
        form = PasswordResetVerifyForm()
    return render(request, 'password_reset_verify.html', {'form': form})


import base64
import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .Reconocimineto.ReconocimientoUsuarios import obtener_rostros_conocidos, comparar_rostros


@csrf_exempt
def save_imagee(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        image_data = data['image'].split(',')[1]
        image_binary = base64.b64decode(image_data)

        # Guardar la imagen temporalmente
        temp_image_path = 'temp_image.png'
        with open(temp_image_path, 'wb') as f:
            f.write(image_binary)

        # Obtener rostros conocidos
        known_faces, known_names = obtener_rostros_conocidos()

        # Comparar rostros
        try:
            match_name = comparar_rostros(known_faces, known_names, temp_image_path)
            if match_name:
                message = f"Rostro coincide con: {match_name}"
            else:
                message = "No se encontró coincidencia."
        except ValueError as e:
            message = str(e)

        # Imprimir el nombre del usuario reconocido
        print(message)

        return JsonResponse({'message': message})
    return JsonResponse({'status': 'error'}, status=400)
