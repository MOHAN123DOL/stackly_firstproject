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
from .serializers import JobSeekerOpenChatSerializer,EmployerOpenChatSerializer, MessageSerializer , SendMessageSerializer  , InboxSerializer
from django.contrib.auth.models import User
from django.db.models import Max, Count, Q

class OpenChatAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]

   
    # Choose serializer by their role
    
    def get_serializer_class(self):
        user = self.request.user

        if hasattr(user, "employee_profile"):
            return EmployerOpenChatSerializer
        return JobSeekerOpenChatSerializer

 
    

    @transaction.atomic # for safe insertion 
    def perform_create(self, serializer):
        user = self.request.user
        job = serializer.validated_data["job"]

       
        #  IF EMPLOYER 
        
        if hasattr(user, "employee_profile"):

            jobseeker = serializer.validated_data.get("jobseeker")

            if not jobseeker:
                raise PermissionDenied("Jobseeker is required.")

            # Check jobseeker applied
            if not UserAppliedJob.objects.filter(
                user=jobseeker,
                job=job
            ).exists():
                raise PermissionDenied("This user did not apply for this job.")

      
        # IF JOBSEEKER 
       
        else:
            jobseeker = user

            if not UserAppliedJob.objects.filter(
                user=user,
                job=job
            ).exists():
                raise PermissionDenied("You must apply first.")

        # Create conversation (1-to-1)
        conversation, _ = Conversation.objects.get_or_create(
            job=job,
            jobseeker=jobseeker
        )

    
        # Add jobseeker participant
       
        ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=jobseeker,
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

        self.conversation = conversation

  
    #  OVERRIDE  CREATE Custom response
   
    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)

        return Response(
            {"conversation_id": self.conversation.id},
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
        return conversation.messages.all().order_by("-created_at")





class InboxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        conversations = Conversation.objects.filter(
            participants__user=user
        ).annotate(
            last_message_time=Max("messages__created_at"),
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
            )
        ).order_by("-last_message_time")

        inbox = []

        for conversation in conversations:
            last_message = conversation.messages.order_by("-created_at").first()
            if not last_message:
                continue

            inbox.append({
                "conversation_id": conversation.id,
                "job_id": conversation.job.id,
                "job_title": conversation.job.role,
                "last_message": last_message.text,
                "last_message_time": conversation.last_message_time,
                "unread_count": conversation.unread_count
            })

        return Response(inbox)
