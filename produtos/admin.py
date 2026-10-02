from django.contrib import admin

from .models import produtosModel


@admin.register(produtosModel)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'preco')
    search_fields = ('id', 'nome', 'descricao')
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
                'fields': ('preco',),
            },
        ),
    )
