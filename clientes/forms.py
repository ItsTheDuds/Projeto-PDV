import re

from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    celular = forms.CharField(
        label='Celular',
        max_length=15,
        widget=forms.TextInput(
            attrs={
                'placeholder': '(00) 00000-0000',
                'inputmode': 'tel',
                'autocomplete': 'tel',
                'maxlength': '15',
            }
        ),
    )

    class Meta:
        model = Cliente
        fields = ['nome', 'celular', 'email']
        labels = {
            'nome': 'Nome do cliente',
            'celular': 'Celular',
            'email': 'E-mail (opcional)',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'cliente@email.com'}),
        }

    def clean_celular(self):
        celular_informado = self.cleaned_data['celular'].strip()

        if not celular_informado:
            raise forms.ValidationError('Informe o número de celular.')

        if not re.fullmatch(r'[0-9()\s+.-]+', celular_informado):
            raise forms.ValidationError(
                'O celular deve conter apenas números e os caracteres de formatação.'
            )

        celular = re.sub(r'\D', '', celular_informado)

        if celular.startswith('55') and len(celular) == 13:
            celular = celular[2:]

        if len(celular) != 11:
            raise forms.ValidationError(
                'Informe o celular com DDD e 11 dígitos, por exemplo: (61) 99999-9999.'
            )

        if celular[0] == '0' or celular[2] != '9':
            raise forms.ValidationError(
                'Informe um celular brasileiro válido com DDD.'
            )

        return celular
