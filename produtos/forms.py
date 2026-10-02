from django import forms
from .models import produtosModel

class produtoForm(forms.ModelForm):
    class Meta:
        model = produtosModel
        fields = ['nome', 'descricao', 'preco', 'quantidade']
        widgets = {
            'descricao': forms.Textarea(
                attrs={
                    'placeholder': 'Descrição opcional',
                    'rows': 3,
                }
            ),
        }
        error_messages = {
            'nome': {
            'required': '',
            },
            'preco': {
            'required': '',
            },
            'quantidade': {
            'required': '',
            },
        }