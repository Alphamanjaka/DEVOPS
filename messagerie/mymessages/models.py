from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User


class Message(models.Model):
    contenu = models.TextField()
    date_envoi = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='owned_messages')
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)
    recipients = models.ManyToManyField(User, blank=True, related_name='received_messages_multi')
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    def __str__(self):
        return self.contenu[:20]
    
    def get_absolute_url(self):
        return reverse("message_detail", kwargs={"pk": self.pk})

    def all_recipients(self):
        users = set()
        if self.recipient:
            users.add(self.recipient)
        for u in self.recipients.all():
            users.add(u)
        return list(users)

    def recipient_display(self):
        names = [u.username for u in self.all_recipients()]
        return ', '.join(names) if names else '—'
    
