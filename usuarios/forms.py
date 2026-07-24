from django import forms
from .models import usuariosModel

class usuarioForm(forms.ModelForm):
    class Meta:
        model = usuariosModel
        fields = ['username', 'email']
        error_messages = {
            'username': {
            'required': '',
            },
            'email': {
            'required': '',
        },
    }