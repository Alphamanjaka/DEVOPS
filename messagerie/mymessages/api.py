import logging

from rest_framework import serializers, viewsets, permissions
from django.db.models import Q, Count
from .models import Message

logger = logging.getLogger(__name__)


class MessageSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True, allow_null=True)
    recipients_username = serializers.SerializerMethodField()
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'contenu', 'date_envoi', 'owner', 'owner_username',
            'recipient', 'recipient_username', 'recipients', 'recipients_username',
            'is_read', 'parent', 'reply_count',
        ]
        read_only_fields = ['owner', 'date_envoi', 'is_read']

    def get_recipients_username(self, obj) -> list[str]:
        usernames = [u.username for u in obj.recipients.all()]
        logger.debug("get_recipients_username for message %s: %s", obj.pk, usernames)
        return usernames


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Message.objects.filter(
            Q(owner=self.request.user) | Q(recipient=self.request.user) | Q(recipients=self.request.user)
        ).select_related('owner', 'recipient').prefetch_related('recipients').annotate(
            reply_count=Count('replies')
        ).order_by('-date_envoi')
        logger.debug("get_queryset for %s: %d messages", self.request.user.username, qs.count())
        return qs

    def perform_create(self, serializer):
        logger.info("API create message by %s", self.request.user.username)
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        obj = self.get_object()
        if obj.owner != self.request.user and not self.request.user.is_superuser:
            logger.warning("API update denied for %s on message %s", self.request.user.username, obj.pk)
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous ne pouvez modifier que vos propres messages.")
        logger.info("API update message %s by %s", obj.pk, self.request.user.username)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner != self.request.user and not self.request.user.is_superuser:
            logger.warning("API delete denied for %s on message %s", self.request.user.username, instance.pk)
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous ne pouvez supprimer que vos propres messages.")
        logger.info("API delete message %s by %s", instance.pk, self.request.user.username)
        instance.delete()
