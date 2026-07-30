import logging

from django.contrib import admin
from .models import Message

logger = logging.getLogger(__name__)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'contenu', 'date_envoi', 'owner', 'recipient', 'is_read', 'parent')
    list_filter = ('is_read', 'date_envoi')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            logger.debug("MessageAdmin get_readonly_fields: editing message pk=%s", obj.pk)
            return ('owner',)
        logger.debug("MessageAdmin get_readonly_fields: creating new message")
        return ()

    def save_model(self, request, obj, form, change):
        if not getattr(obj, 'owner', None):
            obj.owner = request.user
            logger.debug("MessageAdmin save_model: set owner to %s", request.user.username)
        super().save_model(request, obj, form, change)
        action = "updated" if change else "created"
        logger.info("MessageAdmin %s message pk=%s by %s", action, obj.pk, request.user.username)
