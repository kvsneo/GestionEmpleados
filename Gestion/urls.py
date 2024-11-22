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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from Integracion import views

urlpatterns = [
    path('',views.dashboard, name='home'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('error/', views.error_view, name='error'),
    path('create_admin/', views.create_admin, name='create_admin'),
    path('create_manager/', views.create_manager, name='create_manager'),
    path('create_employee/', views.create_employee, name='create_employee'),
    path('list_users/', views.list_users, name='list_users'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('capturarimagenes/', views.capturarimagenes, name='capturarimagenes'),
    path('save_image/', views.save_image, name='save_image'),

    path('index_photos/', views.index_photos, name='index_photos'),

    path('subir_justificante/', views.subir_justificante, name='subir_justificante'),
    path('lista_justificantes/', views.lista_justificantes, name='lista_justificantes'),
    path('editar_justificante/<int:justificante_id>/', views.editar_justificante, name='editar_justificante'),
    path('dashboard/', views.dashboard, name='dashboard'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL1, document_root=settings.MEDIA_ROOT1)
    urlpatterns += static(settings.MEDIA_URL2, document_root=settings.MEDIA_ROOT2)
