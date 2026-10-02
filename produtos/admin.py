from django.contrib import admin

from .models import produtosModel


@admin.register(produtosModel)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'preco', 'quantidade', 'estoque_status')
    search_fields = ('id', 'nome', 'descricao')
    list_filter = ('quantidade',)
    ordering = ('nome',)
    list_per_page = 50

    fieldsets = (
        (
            'Produto',
            {
                'fields': ('nome', 'descricao'),
            },
        ),
        (
            'Comercial',
            {
                'fields': ('preco', 'quantidade'),
            },
        ),
    )

    @admin.display(description='Estoque')
    def estoque_status(self, obj):
        if obj.quantidade <= 0:
            return 'Sem estoque'
        return f'{obj.quantidade} un.'
