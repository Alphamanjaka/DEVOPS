from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['contenu', 'recipient', 'parent']
        widgets = {
            'parent': forms.HiddenInput(),
            'recipient': forms.Select(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Écrivez votre message...'}),
        }
