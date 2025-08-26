# core/serializers.py

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Agent, Post, PostImage, Story, Follow, ChatMessage, Comment, PostLike
from django.conf import settings


# ------------------ Agent ------------------
class AgentSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = ['id', 'name', 'category', 'agent_type', 'description', 'avatar', 'created_at']

    def get_avatar(self, obj):
        return obj.get_avatar()


# ------------------ Post ------------------
class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'uploaded_at']


class PostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'category', 'agent', 'created_at', 'images']


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = ['id', 'user', 'post', 'liked_at']


# ------------------ Story ------------------
class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ['id', 'content', 'type', 'created_at']


# ------------------ Polymorphic helper ------------------
class PolymorphicTargetField(serializers.DictField):
    """
    Handle GenericForeignKey payloads like {"type": "user"|"agent", "id": N}
    """
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        type_map = {
            'user': ContentType.objects.get(app_label='accounts', model='user'),
            'agent': ContentType.objects.get(app_label='core', model='agent'),
        }
        try:
            ct = type_map[data['type'].lower()]
            oid = int(data['id'])
        except Exception:
            raise serializers.ValidationError(
                'Invalid polymorphic reference. Use {"type": "user|agent", "id": <int>}'
            )
        return {'content_type': ct, 'object_id': oid}

    def to_representation(self, value):
        if value is None:
            return None
        model_name = value._meta.model_name
        type_name = 'user' if model_name == 'user' else 'agent'
        return {'type': type_name, 'id': value.pk}


# ------------------ Follow ------------------
class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.PrimaryKeyRelatedField(read_only=True)
    target = PolymorphicTargetField(write_only=True)
    target_repr = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'target', 'target_repr', 'follow_date']

    def get_target_repr(self, obj):
        return PolymorphicTargetField().to_representation(obj.target)

    def create(self, validated_data):
        user = self.context['request'].user
        target_info = validated_data.pop('target')
        return Follow.objects.create(
            follower=user,
            target_content_type=target_info['content_type'],
            target_object_id=target_info['object_id']
        )


# ------------------ ChatMessage ------------------
class ChatMessageSerializer(serializers.ModelSerializer):
    sender = PolymorphicTargetField(read_only=True)
    receiver = PolymorphicTargetField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'receiver', 'type', 'text', 'image_base64', 'is_read', 'created_at']


# ------------------ Comment ------------------
class CommentSerializer(serializers.ModelSerializer):
    sender = PolymorphicTargetField(read_only=True)
    receiver = PolymorphicTargetField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'sender', 'receiver', 'text', 'created_at']
