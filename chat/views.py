from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView , ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .pagination import MessagePagination
from jobseeker.models import Job, UserAppliedJob
from employees.models import Employee

from .models import Conversation, ConversationParticipant, Message
from .serializers import OpenChatSerializer, MessageSerializer
from .utils import can_user_chat





class OpenChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # -------- VALIDATE INPUT --------
        serializer = OpenChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(
            Job,
            id=serializer.validated_data["job_id"]
        )

        # -------- ROLE CHECKS --------
        is_employee = (
            hasattr(request.user, "employee_profile") and
            request.user.employee_profile.company == job.company
        )

        has_applied = can_user_chat(request.user, job)

        # -------- ACCESS CONTROL --------
        if not is_employee and not has_applied:
            return Response(
                {"detail": "Chat not allowed"},
                status=403
            )

        # -------- GET OR CREATE CONVERSATION --------
        conversation, _ = Conversation.objects.get_or_create(
            job=job
        )

        # -------- ALWAYS ADD CURRENT USER --------
        ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=request.user,
            role="EMPLOYER" if is_employee else "JOBSEEKER"
        )

        # -------- ENSURE ALL EMPLOYERS ARE PRESENT --------
        employees = Employee.objects.filter(company=job.company)

        for emp in employees:
            ConversationParticipant.objects.get_or_create(
                conversation=conversation,
                user=emp.user,
                role="EMPLOYER"
            )

        return Response(
            {"conversation_id": conversation.id},
            status=200
        )


class SendMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        text = request.data.get("text")

        if not text:
            return Response(
                {"detail": "Message text required"},
                status=400
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id
        )

        # ---- PARTICIPANT CHECK ----
        if not conversation.participants.filter(
            user=request.user
        ).exists():
            return Response(
                {"detail": "Not allowed"},
                status=403
            )

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            text=text
        )

        return Response(
            MessageSerializer(message).data,
            status=201
        )

class MessageListAPIView(ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = MessagePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation = get_object_or_404(
            Conversation,
            id=self.kwargs["conversation_id"]
        )

        if not conversation.participants.filter(
            user=self.request.user
        ).exists():
            return Message.objects.none()

        return conversation.messages.all()


class MarkMessagesReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get("conversation_id")

        if not conversation_id:
            return Response(
                {"detail": "conversation_id is required"},
                status=400
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id
        )

        # ---- SECURITY: ensure user is participant ----
        if not conversation.participants.filter(
            user=request.user
        ).exists():
            return Response(
                {"detail": "Not allowed"},
                status=403
            )

        # ---- MARK ONLY THIS CONVERSATION AS READ ----
        Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)

        return Response(
            {"detail": "Messages marked as read"},
            status=200
        )
