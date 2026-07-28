from django import forms
from .models import produtosModel

class produtoForm(forms.ModelForm):
    class Meta:
        model = produtosModel
        fields = ['nome', 'descricao', 'preco', 'quantidade']
        error_messages = {
            'nome': {
            'required': '',
            },
            'descricao': {
            'required': '',
            },
            'preco': {
            'required': '',
            },
            'quantidade': {
            'required': '',
            },
        }