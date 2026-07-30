import logging

from django import forms
from django.contrib.auth.models import User
from .models import Message

logger = logging.getLogger(__name__)


class MessageForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Destinataires'
    )

    class Meta:
        model = Message
        fields = ['subject', 'contenu', 'recipient', 'recipients', 'parent']
        widgets = {
            'parent': forms.HiddenInput(),
            'recipient': forms.HiddenInput(),
            'subject': forms.TextInput(attrs={'placeholder': 'Sujet du message (optionnel)'}),
            'contenu': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Écrivez votre message...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipients'].queryset = User.objects.filter(is_active=True)
        if self.instance and self.instance.pk:
            self.fields['recipients'].initial = self.instance.recipients.all()
        if self.initial.get('recipient'):
            self.fields['recipients'].initial = [self.initial['recipient']]
        logger.debug("MessageForm initialized for instance pk=%s", self.instance.pk if self.instance and self.instance.pk else None)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            logger.info("MessageForm saved message pk=%s", instance.pk)
        if self.cleaned_data.get('recipients'):
            instance.recipients.set(self.cleaned_data['recipients'])
            logger.debug("MessageForm set recipients for pk=%s", instance.pk)
        elif commit:
            instance.recipients.clear()
            logger.debug("MessageForm cleared recipients for pk=%s", instance.pk)
        return instance
