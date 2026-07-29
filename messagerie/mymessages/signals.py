from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Message


@receiver(post_save, sender=Message)
def notify_recipient(sender, instance, created, **kwargs):
    if created and instance.recipient and instance.recipient.email:
        send_mail(
            subject=f"Nouveau message de {instance.owner.username}",
            message=f"Vous avez reçu un message de {instance.owner.username} :\n\n{instance.contenu}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.recipient.email],
            fail_silently=True,
        )
