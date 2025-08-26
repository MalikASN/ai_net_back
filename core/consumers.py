import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from .models import ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"] or not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.sender = self.scope["user"]
        self.receiver_id = self.scope["url_route"]["kwargs"]["receiver_id"]
        self.room_name = f"chat_{min(self.sender.id, self.receiver_id)}_{max(self.sender.id, self.receiver_id)}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        msg_type = data.get("type", "TEXT")
        msg_data = data.get("data")

        # persist in DB
        message = await self.save_message(self.sender.id, self.receiver_id, msg_type, msg_data)

        # send to room
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "id": message.id,
                "sender": self.sender.username,
                "receiver_id": self.receiver_id,
                "msg_type": msg_type,
                "data": msg_data,
                "created_at": message.created_at.isoformat(),
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # ---------- DB ops ----------
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, msg_type, msg_data):
        sender_ct = ContentType.objects.get_for_model(User)
        receiver_ct = ContentType.objects.get_for_model(User)

        return ChatMessage.objects.create(
            sender_content_type=sender_ct,
            sender_object_id=sender_id,
            receiver_content_type=receiver_ct,
            receiver_object_id=receiver_id,
            type=msg_type,
            data=msg_data,
        )
