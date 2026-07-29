from django.db.models import Q
from .models import Message


def unread_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            Q(recipient=request.user) | Q(recipients=request.user),
            is_read=False
        ).exclude(owner=request.user).distinct().count()
        return {'unread_count': count}
    return {}
