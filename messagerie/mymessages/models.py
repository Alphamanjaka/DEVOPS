from django.db import models
from django.urls import reverse
from django.utils import timezone


class Message(models.Model):
    contenu = models.TextField()
    date_envoi = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    recipient = models.ForeignKey('auth.User', related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.contenu[:20]
    
    def get_absolute_url(self):
        return reverse("message_detail", kwargs={"pk": self.pk})
    
