from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'celular', 'email', 'criado_em')
    search_fields = ('nome', 'celular', 'email')
