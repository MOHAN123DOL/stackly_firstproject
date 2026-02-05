from rest_framework import serializers
from .models import Conversation, Message


class OpenChatSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()

    class Meta:
        model = Message
        fields = ["id", "sender", "text", "is_read", "created_at"]


