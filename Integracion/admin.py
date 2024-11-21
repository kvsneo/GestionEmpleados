from django.contrib import admin
from django.http import HttpResponseForbidden

# Register your models here.

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin():
            return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def manager_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_manager():
            return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
