from django.db import models
from django.urls import reverse


class Message(models.Model):
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.contenu[:20]
    
    def get_absolute_url(self):
        return reverse("message_detail", kwargs={"pk": self.pk})
    
