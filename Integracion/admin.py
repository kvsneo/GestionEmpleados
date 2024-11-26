from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from Integracion.models import CustomUser

# Registra tus modelos aquí.

def admin_required(view_func):
    """
    Decorador para asegurar que el usuario esté autenticado y tenga el rol de administrador.

    Args:
        view_func (function): La función de vista a decorar.

    Returns:
        function: La función de vista envuelta.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            return HttpResponseRedirect(f"{reverse('error')}?username={request.user.username}&role={request.user.role}")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def manager_required(view_func):
    """
    Decorador para asegurar que el usuario esté autenticado y tenga el rol de gerente.

    Args:
        view_func (function): La función de vista a decorar.

    Returns:
        function: La función de vista envuelta.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'manager':
            return HttpResponseRedirect(f"{reverse('error')}?username={request.user.username}&role={request.user.role}")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def admin_or_manager_required(view_func):
    """
    Decorador para asegurar que el usuario esté autenticado y tenga el rol de administrador o gerente.

    Args:
        view_func (function): La función de vista a decorar.

    Returns:
        function: La función de vista envuelta.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_admin() or request.user.is_manager()):
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(f"{reverse('error')}?username={request.user.username}&role={request.user.role}")

    return _wrapped_view


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Opciones de la interfaz de administración para el modelo CustomUser.
    """
    list_display = ('username', 'email', 'role')
    search_fields = ('username', 'email')
    list_filter = ('role',)