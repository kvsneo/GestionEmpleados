"""
URL configuration for Gestion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings  # Importa la configuración de Django
from django.conf.urls.static import static  # Importa la función para servir archivos estáticos
from django.contrib import admin  # Importa el módulo de administración de Django
from django.contrib.auth import views as auth_views  # Importa las vistas de autenticación de Django
from django.urls import path  # Importa la función path para definir rutas

from Integracion import views  # Importa las vistas del módulo Integracion

urlpatterns = [
    path('', views.dashboard, name='home'),  # Ruta para el dashboard
    path('admin/', admin.site.urls),  # Ruta para la administración
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # Ruta para el login
    path('logout/', views.custom_logout, name='logout'),  # Ruta para el logout
    path('error/', views.error_view, name='error'),  # Ruta para la vista de error
    path('create_admin/', views.create_admin, name='create_admin'),  # Ruta para crear un administrador
    path('create_manager/', views.create_manager, name='create_manager'),  # Ruta para crear un manager
    path('create_employee/', views.create_employee, name='create_employee'),  # Ruta para crear un empleado
    path('list_users/', views.list_users, name='list_users'),  # Ruta para listar usuarios
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),  # Ruta para editar un usuario
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),  # Ruta para eliminar un usuario
    path('capturarimagenes/', views.capturarimagenes, name='capturarimagenes'),  # Ruta para capturar imágenes
    path('get_remaining_images/', views.get_remaining_images, name='get_remaining_images'),
    # Ruta para obtener imágenes restantes
    path('save_image/', views.save_image, name='save_image'),  # Ruta para guardar una imagen
    path('index_photos/', views.index_photos, name='index_photos'),  # Ruta para indexar fotos
    path('subir_justificante/', views.subir_justificante, name='subir_justificante'),  # Ruta para subir justificantes
    path('lista_justificantes/', views.lista_justificantes, name='lista_justificantes'),
    # Ruta para listar justificantes
    path('editar_justificante/<int:justificante_id>/', views.editar_justificante, name='editar_justificante'),
    # Ruta para editar justificantes
    path('dashboard/', views.dashboard, name='dashboard'),  # Ruta para el dashboard
    path('edit_employee_profile/', views.edit_employee_profile, name='edit_employee_profile'),
    # Ruta para editar perfil de empleado
    path('change_password/', views.change_password, name='change_password'),  # Ruta para cambiar contraseña
    path('change_schedule/', views.change_schedule, name='change_schedule'),  # Ruta para cambiar horario
    path('BuscarImagenes/', views.buscar_imagenes, name='BuscarImagenes'),  # Ruta para buscar imágenes
    path('EliminarImagen/<str:nombre_usuario>/<str:nombre_imagen>/', views.eliminar_imagen, name='EliminarImagen'),
    # Ruta para eliminar imagen
    path('ReconocimientoUsuarios/', views.reconocimiento_usuarios, name='ReconocimientoUsuarios'),
    # Ruta para reconocimiento de usuarios
    path('reportes/', views.reportes, name='reportes'),  # Ruta para reportes
    path('reporte_justificantes/', views.reporte_justificantes, name='reporte_justificantes'),
    # Ruta para reporte de justificantes
    path('reporte_solicitudes/', views.reporte_solicitudes, name='reporte_solicitudes'),
    # Ruta para reporte de solicitudes
    path('password_reset/', views.password_reset_request, name='password_reset_request'),
    # Ruta para solicitud de restablecimiento de contraseña
    path('password_reset_verify/', views.password_reset_verify, name='password_reset_verify'),
    # Ruta para verificar restablecimiento de contraseña
    path('save_imagee/', views.save_imagee, name='save_imagee'),  # Ruta para guardar imagen
    path('reporte-inasistencias/', views.reporte_inasistencias, name='reporte_inasistencias'),
    # Ruta para reporte de inasistencias
    path('reporte/porcentajes/', views.reporte_porcentajes_asistencias, name='reporte_porcentajes_asistencias'),
    # Ruta para reporte de porcentajes de asistencias
    path('horarios/', views.ver_horarios, name='horarios'),  # Ruta para ver horarios
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL1,
                          document_root=settings.MEDIA_ROOT1)  # Sirve archivos estáticos en modo debug
    urlpatterns += static(settings.MEDIA_URL2,
                          document_root=settings.MEDIA_ROOT2)  # Sirve archivos estáticos en modo debug
