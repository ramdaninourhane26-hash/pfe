# consultations/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message
from nutritionists.models import Notification

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        # Vérifier si l'utilisateur est authentifié
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Récupérer l'ID de l'autre utilisateur
        self.other_user_id = self.scope['url_route']['kwargs'].get('user_id')
        
        # Créer un nom de room unique (trié pour éviter doublon)
        user_ids = sorted([self.user.id, self.other_user_id])
        self.room_name = f'chat_{user_ids[0]}_{user_ids[1]}'
        self.room_group_name = f'chat_{self.room_name}'
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Marquer les messages comme lus
        await self.mark_messages_as_read()
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            content = data.get('content', '')
            receiver_id = data.get('receiver_id')
            
            if content and receiver_id:
                # Sauvegarder le message
                message = await self.save_message(receiver_id, content)
                
                # Envoyer au groupe
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender_id': message.sender.id,
                            'sender_name': message.sender.get_full_name(),
                            'created_at': message.created_at.isoformat(),
                            'time_display': message.created_at.strftime('%H:%M'),
                            'is_mine': False
                        }
                    }
                )
                
                # Notifier l'autre utilisateur (push notification)
                await self.notify_user(receiver_id, content)
                
        elif message_type == 'typing':
            # Notifier que l'utilisateur est en train d'écrire
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_notification',
                    'is_typing': data.get('is_typing', False),
                    'user_name': self.user.get_full_name()
                }
            )
    
    async def chat_message(self, event):
        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'is_typing': event['is_typing'],
            'user_name': event['user_name']
        }))
    
    @database_sync_to_async
    def save_message(self, receiver_id, content):
        receiver = User.objects.get(id=receiver_id)
        message = Message.objects.create(
            sender=self.user,
            receiver=receiver,
            content=content
        )
        
        # Créer une notification pour le destinataire
        if receiver.role == 'nutritionist':
            Notification.objects.create(
                nutritionist=receiver,
                notification_type='new_message',
                title='💬 New Message',
                message=f'{self.user.get_full_name()} sent you a message.',
                related_patient=self.user,
                related_id=message.id,
                is_read=False
            )
        
        return message
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        if self.other_user_id:
            Message.objects.filter(
                sender_id=self.other_user_id,
                receiver=self.user,
                is_read=False
            ).update(is_read=True)
    
    @database_sync_to_async
    def notify_user(self, receiver_id, content):
        # Notification en base de données
        try:
            receiver = User.objects.get(id=receiver_id)
            Notification.objects.create(
                user=receiver if receiver.role == 'patient' else None,
                nutritionist=receiver if receiver.role == 'nutritionist' else None,
                notification_type='new_message',
                title='💬 New Message',
                message=f'{self.user.get_full_name()}: {content[:50]}...',
                related_patient=self.user if self.user.role == 'patient' else None,
                related_id=None,
                is_read=False
            )
        except Exception as e:
            print(f"Error creating notification: {e}")