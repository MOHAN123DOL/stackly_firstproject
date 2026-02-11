from rest_framework import serializers
from .models import Conversation, Message
from jobseeker.models import Job, UserAppliedJob
from django.contrib.auth.models import User


class OpenChatSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.none())
    jobseeker = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context["request"]
        user = request.user

        # ----------------------
        # EMPLOYEE LOGIN
        # ----------------------
        if hasattr(user, "employee_profile"):

            # Only show company jobs
            self.fields["job"].queryset = Job.objects.filter(
                company=user.employee_profile.company
            )

            # Jobseeker dropdown will be filtered later in view
            self.fields["jobseeker"].queryset = User.objects.all()

        # ----------------------
        # JOBSEEKER LOGIN
        # ----------------------
        else:

            # Only show jobs the user applied to
            self.fields["job"].queryset = Job.objects.filter(
                userappliedjob__user=user
            ).distinct()

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        is_employee = hasattr(user, "employee_profile")

        if is_employee and not data.get("jobseeker"):
            raise serializers.ValidationError(
                {"jobseeker": "This field is required for employees."}
            )

        if not is_employee and data.get("jobseeker"):
            raise serializers.ValidationError(
                {"jobseeker": "Jobseekers should not send this field."}
            )

        return data
    
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
