import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from channels.layers import get_channel_layer
from .models import Message

logger = logging.getLogger(__name__)


def _notify_websocket(instance):
    recipients = instance.all_recipients()
    if not recipients:
        logger.debug("notify_websocket: no recipients for message pk=%s", instance.pk)
        return
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("notify_websocket: no channel layer configured for message pk=%s", instance.pk)
            return
        for user in recipients:
            if user == instance.owner:
                continue
            channel_layer.group_send(
                f'notify_{user.username}',
                {
                    'type': 'new_message',
                    'message_id': instance.pk,
                    'from': instance.owner.username,
                    'preview': instance.contenu[:80],
                    'timestamp': instance.date_envoi.strftime('%H:%M'),
                }
            )
            logger.info("notify_websocket: sent to %s for message pk=%s", user.username, instance.pk)
    except Exception as e:
        logger.error("notify_websocket: failed for message pk=%s: %s", instance.pk, e)


@receiver(post_save, sender=Message)
def notify_recipient(sender, instance, created, **kwargs):
    if not created:
        return
    logger.info("notify_recipient: signal fired for message pk=%s from %s", instance.pk, instance.owner.username)
    if instance.recipient and instance.recipient.email:
        logger.info("notify_recipient: sending email to %s for message pk=%s", instance.recipient.email, instance.pk)
        send_mail(
            subject=f"Nouveau message de {instance.owner.username}",
            message=f"Vous avez reçu un message de {instance.owner.username} :\n\n{instance.contenu}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.recipient.email],
            fail_silently=True,
        )
        logger.info("notify_recipient: email sent to %s", instance.recipient.email)
    else:
        logger.debug("notify_recipient: no email for message pk=%s (no recipient or no email)", instance.pk)
    _notify_websocket(instance)
