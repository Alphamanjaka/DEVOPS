import logging

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class Message(models.Model):
    subject = models.CharField(max_length=255, blank=True, default='')
    contenu = models.TextField()
    date_envoi = models.DateTimeField(default=timezone.now, db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='owned_messages', db_index=True)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    recipients = models.ManyToManyField(User, blank=True, related_name='received_messages_multi')
    is_read = models.BooleanField(default=False, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    def __str__(self):
        return self.contenu[:20]

    def get_absolute_url(self):
        url = reverse("message_detail", kwargs={"pk": self.pk})
        logger.debug("get_absolute_url for Message %s: %s", self.pk, url)
        return url

    def all_recipients(self):
        users = set()
        if self.recipient:
            users.add(self.recipient)
        for u in self.recipients.all():
            users.add(u)
        logger.debug("all_recipients for Message %s: %s users", self.pk, len(users))
        return list(users)

    def recipient_display(self):
        names = [u.username for u in self.all_recipients()]
        result = ', '.join(names) if names else '—'
        logger.debug("recipient_display for Message %s: %s", self.pk, result)
        return result
    
