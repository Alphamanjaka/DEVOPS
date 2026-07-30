import logging

from django.db.models import Q
from .models import Message

logger = logging.getLogger(__name__)


def unread_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            Q(recipient=request.user) | Q(recipients=request.user),
            is_read=False
        ).exclude(owner=request.user).distinct().count()
        logger.debug("unread_count for %s: %s", request.user.username, count)
        return {'unread_count': count}
    logger.debug("unread_count: user not authenticated")
    return {}
