from django.contrib import admin
from .models import Message

# Register your models here.


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('contenu', 'date_envoi', 'owner', 'recipient')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si l'objet existe (modification), on rend 'owner' non modifiable
            return ('owner',)
        return ()  # Sinon (création), on laisse le champ modifiable

    def save_model(self, request, obj, form, change):
        # Si c'est une création et que le propriétaire n'est pas défini
        if not getattr(obj, 'owner', None):
            obj.owner = request.user
        super().save_model(request, obj, form, change)
