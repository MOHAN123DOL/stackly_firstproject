from rest_framework import serializers
from .models import Conversation, Message
from jobseeker.models import Job, UserAppliedJob
from django.contrib.auth.models import User




class JobSeekerOpenChatSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.context["request"].user

        # Only jobs this user applied to
        self.fields["job"].queryset = Job.objects.filter(
            userappliedjob__user=user
        ).distinct()


class EmployerOpenChatSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.none())
    jobseeker = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.context["request"].user
        company = user.employee_profile.company

        company_jobs = Job.objects.filter(company=company)

        # Only company jobs
        self.fields["job"].queryset = company_jobs

        # Only jobseekers who applied to company jobs
        self.fields["jobseeker"].queryset = User.objects.filter(
            userappliedjob__job__in=company_jobs
        ).distinct()
            
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
        read_only_fields = ["is_read"]




class InboxSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    last_message = serializers.CharField()
    last_message_time = serializers.DateTimeField()
    unread_count = serializers.IntegerField()
