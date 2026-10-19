from decimal import Decimal

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from vendas.models import ItemVenda, Venda


class AutorizacaoEdicaoFiadoForm(forms.Form):
    revisao = forms.CharField(widget=forms.HiddenInput)
    senha = forms.CharField(
        label='Senha do administrador',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        help_text='Use a mesma senha utilizada para quitar o fiado.',
    )


class ItemFiadoForm(forms.ModelForm):
    quantidade = forms.IntegerField(min_value=1, max_value=2147483647)
    preco_unitario = forms.DecimalField(
        label='Preço unitário', min_value=Decimal('0.01'),
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
    )

    class Meta:
        model = ItemVenda
        fields = ('produto', 'quantidade', 'preco_unitario')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = self.fields['produto'].queryset.order_by('nome')
        for nome, campo in self.fields.items():
            campo.widget.attrs['aria-label'] = campo.label or nome.capitalize()


class BaseItensFiadoFormSet(BaseInlineFormSet):
    def __init__(self, *args, valor_pago=Decimal('0.00'), **kwargs):
        self.valor_pago = valor_pago
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        # Todos os itens atuais devem ser enviados, inclusive os marcados para
        # remoção. Impede IDs de outra compra ou omissões no management form.
        ids_atuais = set(self.get_queryset().values_list('pk', flat=True))
        ids_enviados = [
            form.cleaned_data['id'].pk
            for form in self.forms
            if form.cleaned_data.get('id') is not None
        ]
        if (
            self.initial_form_count() != len(ids_atuais)
            or len(ids_enviados) != len(ids_atuais)
            or set(ids_enviados) != ids_atuais
            or any(not form.cleaned_data.get('id') for form in self.initial_forms)
            or any(form.cleaned_data.get('id') for form in self.extra_forms)
        ):
            raise forms.ValidationError('Os itens da compra mudaram ou são inválidos. Recarregue a edição.')

        itens = [
            form.cleaned_data for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]
        self.total = sum(
            (item['quantidade'] * item['preco_unitario'] for item in itens),
            Decimal('0.00'),
        )
        if self.total > Decimal('9999999999.99'):
            raise forms.ValidationError('O valor total excede o limite permitido para a compra.')
        if self.total < self.valor_pago:
            raise forms.ValidationError('O valor da compra não pode ser menor que o valor já pago.')


ItensFiadoFormSet = inlineformset_factory(
    Venda, ItemVenda, form=ItemFiadoForm, formset=BaseItensFiadoFormSet,
    extra=0, can_delete=True, max_num=1000, validate_max=True, absolute_max=1000,
)
