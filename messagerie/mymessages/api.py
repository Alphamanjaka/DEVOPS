from rest_framework import serializers, viewsets, permissions
from django.db.models import Q
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True, allow_null=True)
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'contenu', 'date_envoi', 'owner', 'owner_username',
            'recipient', 'recipient_username', 'is_read', 'parent', 'reply_count',
        ]
        read_only_fields = ['owner', 'date_envoi', 'is_read']

    def get_reply_count(self, obj) -> int:
        return obj.replies.count()


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            Q(owner=self.request.user) | Q(recipient=self.request.user)
        ).select_related('owner', 'recipient').order_by('-date_envoi')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
