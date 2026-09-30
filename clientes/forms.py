from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'celular', 'email']
        labels = {
            'nome': 'Nome do cliente',
            'celular': 'Celular',
            'email': 'E-mail (opcional)',
        }
        widgets = {
            'celular': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'placeholder': 'cliente@email.com'}),
        }

    def clean_celular(self):
        celular = self.cleaned_data['celular'].strip()
        if not celular:
            raise forms.ValidationError('Informe o número de celular.')
        return celular
