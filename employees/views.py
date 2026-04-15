from rest_framework.generics import GenericAPIView ,CreateAPIView , ListAPIView ,RetrieveUpdateDestroyAPIView , RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.generics import mixins
from datetime import timedelta
from jobseeker.tasks import send_interview_reminder
from rest_framework import status
from django.contrib.auth.models import User 
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from jobseeker.models import Job , JobCategory , resumetoggle
import random
from .models import PasswordResetOTP , Interview , Employee
from django.utils.timezone import now
from .serializers import (ResetPasswordWithOTPSerializer , JobCategorySerializer 
                          , EmployeeRegistrationSerializer ,
                          EmployerUpdateStatusSerializer,EmployerForgotPasswordOTPSerializer ,JobCreateSerializer,InterviewSerializer , EmployerApplicationListSerializer )
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError , PermissionDenied
from jobseeker.models import UserAppliedJob , Company , Job , JobSeeker
from chat.models import Conversation,ConversationParticipant , Message
from rest_framework.permissions import AllowAny



#FOR SIGNUP PAGE 

class EmployeeRegistrationAPI(CreateAPIView):

    serializer_class = EmployeeRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()

        return Response(
            {
                "message": "Employer registration successful.",
                "data": {
                    "username": employee.user.username,
                    "email": employee.user.email,
                    "company": employee.company.name,
                    "role": employee.role,
                
                },
            "Login_link":"/login/all/"
            },
            status=status.HTTP_201_CREATED
        )



#FOR FORGOT PASSWORD AND GET TOKEN LINK AND ALLOW USER CREATE NEW PASSWORD

class EmployerForgotPasswordOTPAPI(GenericAPIView):
    serializer_class = EmployerForgotPasswordOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email, is_staff=True)

        otp = str(random.randint(100000, 999999))

        PasswordResetOTP.objects.create(
            user=user,
            otp=otp
        )

       
        print("PASSWORD RESET OTP:", otp)

        return Response(
            {"message": "OTP sent to your email"},
            status=status.HTTP_200_OK
        )




class ResetPasswordWithOTPAPI(GenericAPIView):
    serializer_class = ResetPasswordWithOTPSerializer
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.filter(email=email, is_staff=True).first()
        if not user:
            return Response(
                {"error": "Invalid email"},
                status=status.HTTP_400_BAD_REQUEST
            )

        record = PasswordResetOTP.objects.filter(
            user=user,
            otp=otp
        ).last()

        if not record:
            return Response(
                {"error": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if record.is_expired():
            return Response(
                {"error": "OTP expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()


        PasswordResetOTP.objects.filter(user=user).delete()

        return Response(
            {"message": "Password reset successful. Please login."},
            status=status.HTTP_200_OK
        )



class JobCreateAPIView(CreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

#for job category crud

class JobCategoryCreateAPIView(CreateAPIView):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [IsAuthenticated , IsAdminUser]

class JobCategoryAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = JobCategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = JobCategory.objects.all()


class ScheduleInterviewAPIView(CreateAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Interview.objects.none()

    def _get_employee_company_id(self):
        if not hasattr(self, "_employee_company_id"):
            self._employee_company_id = Employee.objects.filter(
                user_id=self.request.user.id
            ).values_list("company_id", flat=True).first()
        return self._employee_company_id

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["company_id"] = self._get_employee_company_id()
        return context

    def perform_create(self, serializer):

        user_id = self.request.user.id

        # ✅ 1 QUERY — get employee + company_id only
        company_id = self._get_employee_company_id()
        if not company_id:
            raise ValidationError("You are not an employee.")

        job = serializer.validated_data["job"]
        jobseeker = serializer.validated_data["jobseeker"]

       

        if job.company_id != company_id:
            raise ValidationError("Invalid job access.")

        
        if not UserAppliedJob.objects.filter(
            job_id=job.id,
            user_id=jobseeker.user_id
        ).exists():
            raise ValidationError("Candidate not applied.")

       
        interview = serializer.save(scheduled_by_id=user_id)

       
        reminder_time = interview.interview_date - timedelta(hours=1)

        if reminder_time > now():
            send_interview_reminder.apply_async(
                args=[interview.id],
                eta=reminder_time
            )

        
        conversation, _ = Conversation.objects.get_or_create(
            job_id=job.id,
            jobseeker_id=jobseeker.user_id
        )

        
        employee_user_ids = list(
            Employee.objects.filter(
                company_id=company_id
            ).values_list("user_id", flat=True)
        )

        
        participants = [
            ConversationParticipant(
                conversation_id=conversation.id,
                user_id=uid,
                role="EMPLOYER"
            )
            for uid in employee_user_ids
        ]

       
        ConversationParticipant.objects.bulk_create(
            participants,
            ignore_conflicts=True
        )

        
        ConversationParticipant.objects.get_or_create(
            conversation_id=conversation.id,
            user_id=jobseeker.user_id,
            role="JOBSEEKER"
        )

       
        Message.objects.create(
            conversation_id=conversation.id,
            sender_id=user_id,
            text=f"Interview Scheduled! Job: {job.role} Date: {interview.interview_date}"
        )
class EmployerJobApplicationsAPIView(ListAPIView):
    serializer_class = EmployerApplicationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        if not hasattr(self.request.user, "employee_profile"):
            raise PermissionDenied("Only employer can access this.")

        job_id = self.kwargs.get("job_id")

        job = Job.objects.get(id=job_id)


        # Check employer belongs to same company
        if job.company != self.request.user.employee_profile.company:
            raise PermissionDenied("Not allowed for this job.")
        UserAppliedJob.objects.filter(
            job=job,
            status="APPLIED"
        ).update(status="UNDER_REVIEW")
        return UserAppliedJob.objects.filter(job=job).select_related(
            "user",
            "user__jobseeker"
        )
    
class EmployerUpdateApplicationStatusAPIView(RetrieveUpdateAPIView):
    serializer_class = EmployerUpdateStatusSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserAppliedJob.objects.all()

    def get_object(self):
        application = super().get_object()

        if not hasattr(self.request.user, "employee_profile"):
            raise PermissionDenied("Only employer allowed.")

        if application.job.company != self.request.user.employee_profile.company:
            raise PermissionDenied("Not allowed for this job.")

        return application

    def perform_update(self, serializer):
        old_status = self.get_object().status
        application = serializer.save()

        # Only send message if status changed
        if old_status != application.status:

            # 🔹 Get or create conversation
            conversation, _ = Conversation.objects.get_or_create(
                job=application.job,
                jobseeker=application.user
            )

            # 🔹 Add jobseeker as participant
            ConversationParticipant.objects.get_or_create(
                conversation=conversation,
                user=application.user,
                role="JOBSEEKER"
            )

            # 🔹 Add all company employees as participants
            employees = Employee.objects.filter(
                company=application.job.company
            )

            for emp in employees:
                ConversationParticipant.objects.get_or_create(
                    conversation=conversation,
                    user=emp.user,
                    role="EMPLOYER"
                )

            # 🔹 Create automatic message
            Message.objects.create(
                conversation=conversation,
                sender=self.request.user,
                text=f"Your application status has been updated to {application.status}."
            )

class ResumeDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        user_id = pk

        jobseeker =JobSeeker.objects.select_related("user").get(user_id=user_id)
        if not jobseeker:
            return Response({"message": "jobseeker is not found"},status=status.HTTP_404_NOT_FOUND)       
        if not jobseeker.resume:
            return Response(
                {"message": "Resume not uploaded"},
                status=status.HTTP_404_NOT_FOUND
            )
        choice = resumetoggle.objects.filter(user_id=user_id).first()
        if not choice:
            return Response({"message": "Resume settings not found"},status=status.HTTP_404_NOT_FOUND)
        if choice.is_private:
            return Response({"message": "User has hidden their resume"},status=status.HTTP_403_FORBIDDEN)
        if choice.is_public:
            return Response(
                {
                    "message": "fetch sucessfully",
                    "resume_url": jobseeker.resume.url
                },
                status=status.HTTP_200_OK
            )
        if choice.is_recruiters_only:
            company = Company.objects.filter(employees__user=request.user).first()
            if not company:
                return Response(
                    {"message": "Employer company not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            has_applied = UserAppliedJob.objects.filter(
                user_id=user_id,
                job__company=company
            ).exists()

            if not has_applied:
                return Response({"message": "Access denied: User did not apply to your jobs"},status=status.HTTP_403_FORBIDDEN)
            return Response(
                {
                    "message": "fetch successfully ",
                    "resume_url": jobseeker.resume.url
                },
                status=status.HTTP_200_OK
            )
        
        

