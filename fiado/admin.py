from django.contrib import admin

from .models import ConfiguracaoFiado, Fiado


@admin.register(Fiado)
class FiadoAdmin(admin.ModelAdmin):
    list_display = ('venda', 'cliente', 'pago', 'pago_em')
    list_filter = ('pago',)

    @admin.display(description='Cliente')
    def cliente(self, obj):
        return obj.venda.cliente


@admin.register(ConfiguracaoFiado)
class ConfiguracaoFiadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'atualizado_em')

    def has_add_permission(self, request):
        return not ConfiguracaoFiado.objects.exists()
