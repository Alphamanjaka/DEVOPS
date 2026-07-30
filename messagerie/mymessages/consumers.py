import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from .models import Message

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f'notify_{self.user.username}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("Notification WebSocket connected: user=%s", self.user.username)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("Notification WebSocket disconnected: user=%s code=%s", self.user, close_code)

    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message_id': event['message_id'],
            'from': event['from'],
            'preview': event['preview'],
            'timestamp': event['timestamp'],
        }))


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            logger.warning("WebSocket connection rejected: unauthenticated user")
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info("WebSocket connected: user=%s room=%s", self.user.username, self.room_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info("WebSocket disconnected: user=%s room=%s code=%s", self.user, self.room_name, close_code)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data['message']
        recipient_username = data['recipient']

        new_message = await self.save_message(message_content, recipient_username)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': new_message.contenu,
                'owner': self.user.username,
                'timestamp': new_message.date_envoi.strftime('%H:%M'),
            }
        )
        logger.info("Message sent: user=%s room=%s", self.user.username, self.room_name)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'owner': event['owner'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, content, recipient_username):
        recipient = User.objects.get(username=recipient_username)
        msg = Message.objects.create(
            contenu=content,
            owner=self.user,
            recipient=recipient
        )
        return msg
