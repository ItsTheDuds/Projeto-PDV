from django.contrib import admin

from .models import (
    AplicacaoRecebimento,
    ConfiguracaoFiado,
    Fiado,
    RecebimentoFiado,
)


@admin.register(Fiado)
class FiadoAdmin(admin.ModelAdmin):
    list_display = ('venda', 'cliente', 'valor_pago', 'saldo', 'pago', 'pago_em')
    list_filter = ('pago',)

    @admin.display(description='Cliente')
    def cliente(self, obj):
        return obj.venda.cliente

    @admin.display(description='Saldo')
    def saldo(self, obj):
        return obj.saldo_devedor


@admin.register(RecebimentoFiado)
class RecebimentoFiadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'valor_total', 'usuario', 'criado_em')
    search_fields = ('cliente__nome', 'cliente__celular')
    ordering = ('-criado_em',)


@admin.register(AplicacaoRecebimento)
class AplicacaoRecebimentoAdmin(admin.ModelAdmin):
    list_display = ('recebimento', 'fiado', 'valor')


@admin.register(ConfiguracaoFiado)
class ConfiguracaoFiadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'atualizado_em')

    def has_add_permission(self, request):
        return not ConfiguracaoFiado.objects.exists()
