from django.contrib import admin

from .models import ItemVenda, Venda


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'forma_pagamento', 'total', 'criada_em')
    list_filter = ('forma_pagamento', 'criada_em')
    inlines = [ItemVendaInline]
