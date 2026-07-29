from rest_framework import serializers, viewsets, permissions
from django.db.models import Q
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True, allow_null=True)
    recipients_username = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'contenu', 'date_envoi', 'owner', 'owner_username',
            'recipient', 'recipient_username', 'recipients', 'recipients_username',
            'is_read', 'parent', 'reply_count',
        ]
        read_only_fields = ['owner', 'date_envoi', 'is_read']

    def get_reply_count(self, obj) -> int:
        return obj.replies.count()

    def get_recipients_username(self, obj):
        return [u.username for u in obj.recipients.all()]


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            Q(owner=self.request.user) | Q(recipient=self.request.user) | Q(recipients=self.request.user)
        ).select_related('owner', 'recipient').prefetch_related('recipients').order_by('-date_envoi')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
