from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView , ListAPIView , CreateAPIView
from rest_framework.exceptions import PermissionDenied 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .pagination import MessagePagination
from jobseeker.models import Job, UserAppliedJob
from employees.models import Employee
from django.db import transaction
from .models import Conversation, ConversationParticipant, Message
from .serializers import OpenChatSerializer, MessageSerializer , SendMessageSerializer  , InboxSerializer
from django.contrib.auth.models import User



class OpenChatAPIView(GenericAPIView):
    serializer_class = OpenChatSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = serializer.validated_data["job"]
        jobseeker_user = serializer.validated_data.get("jobseeker")

        user = request.user

        # -----------------------------------
        # JOBSEEKER FLOW
        # -----------------------------------
        if not hasattr(user, "employee_profile"):

            if not UserAppliedJob.objects.filter(
                user=user,
                job=job
            ).exists():
                raise PermissionDenied("You must apply first.")

            jobseeker_user = user

        # -----------------------------------
        # EMPLOYEE FLOW
        # -----------------------------------
        else:
            employee = user.employee_profile

            if job.company != employee.company:
                raise PermissionDenied("Not your company job.")

            if not UserAppliedJob.objects.filter(
                user=jobseeker_user,
                job=job
            ).exists():
                raise PermissionDenied("Candidate did not apply.")

        # -----------------------------------
        # CREATE PRIVATE CONVERSATION
        # -----------------------------------
        conversation, _ = Conversation.objects.get_or_create(
            job=job,
            jobseeker=jobseeker_user
        )

        # Add jobseeker participant
        ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=jobseeker_user,
            role="JOBSEEKER"
        )

        # Add all company employees
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
class SendMessageAPIView(CreateAPIView):
    serializer_class = SendMessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        conversation = get_object_or_404(
            Conversation,
            id=serializer.validated_data["conversation_id"]
        )

        if not conversation.participants.filter(
            user=self.request.user
        ).exists():
            raise PermissionDenied("Not allowed")

        self.message = Message.objects.create(
            conversation=conversation,
            sender=self.request.user,
            text=serializer.validated_data["text"]
        )

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            MessageSerializer(self.message).data,
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

        # Check participant
        if not conversation.participants.filter(
            user=self.request.user
        ).exists():
            return Message.objects.none()

        # 🔥 Mark messages as read automatically
        Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(
            sender=self.request.user
        ).update(is_read=True)

        # Return all messages
        return conversation.messages.all()



class InboxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        conversations = Conversation.objects.filter(
            participants__user=user
        ).distinct()

        inbox = []

        for conversation in conversations:
            last_message = conversation.messages.order_by("-created_at").first()
            if not last_message:
                continue

            unread_count = conversation.messages.filter(
                is_read=False
            ).exclude(sender=user).count()

            inbox.append({
                "conversation_id": conversation.id,
                "job_id": conversation.job.id,
                "job_title": conversation.job.role,
                "last_message": last_message.text,
                "last_message_time": last_message.created_at,
                "unread_count": unread_count
            })

        inbox.sort(key=lambda x: x["last_message_time"], reverse=True)

        return Response(inbox)