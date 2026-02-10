from rest_framework import serializers
from .models import Conversation, Message


class OpenChatSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "text",
            "created_at",
            "is_read"
        ]
        read_only_fields = ["id", "sender", "created_at"]

class SendMessageSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    text = serializers.CharField()

    class Meta:
        model = Message
        fields = ["id", "sender", "text", "is_read", "created_at"]





class InboxSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    last_message = serializers.CharField()
    last_message_time = serializers.DateTimeField()
    unread_count = serializers.IntegerField()
