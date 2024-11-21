from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from Integracion.models import CustomUser


# Register your models here.

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            return HttpResponseRedirect(f"{reverse('error')}?username={request.user.username}&role={request.user.role}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

#Ordena la informacion en admin de django

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    search_fields = ('username', 'email')
    list_filter = ('role',)