from rest_framework.generics import GenericAPIView ,CreateAPIView , ListAPIView ,RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User 
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from jobseeker.models import Job , JobCategory
import random
from .models import PasswordResetOTP , Interview , Employee
from django.utils.timezone import now
from .serializers import (ResetPasswordWithOTPSerializer , JobCategorySerializer 
                          , EmployeeRegistrationSerializer ,EmployerForgotPasswordOTPSerializer ,JobCreateSerializer,InterviewSerializer )
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
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

    def perform_create(self, serializer):

        job = serializer.validated_data["job"]
        jobseeker = serializer.validated_data["jobseeker"]

        # 1️⃣ Check logged-in user is employee of job company
        is_employee = Employee.objects.filter(
            user=self.request.user,
            company=job.company
        ).exists()

        if not is_employee:
            raise ValidationError("You cannot schedule interview for this job.")

        # 2️⃣ Check candidate applied (IMPORTANT FIX)
        applied = UserAppliedJob.objects.filter(
            job=job,
            user=jobseeker.user   # ✅ correct
        ).exists()

        if not applied:
            raise ValidationError("This candidate did not apply for this job.")

        # 3️⃣ Save interview
        interview = serializer.save(scheduled_by=self.request.user)

        jobseeker_user = jobseeker.user   # ✅ correct
        employer_user = self.request.user

        # 4️⃣ Get or create conversation
        conversation, _ = Conversation.objects.get_or_create(
            job=job,
            jobseeker=jobseeker_user
        )

        # 5️⃣ Add participants
        ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=jobseeker_user,
            role="JOBSEEKER"
        )

        employees = Employee.objects.filter(company=job.company)

        for emp in employees:
            ConversationParticipant.objects.get_or_create(
                conversation=conversation,
                user=emp.user,
                role="EMPLOYER"
            )

        # 6️⃣ Create system message
        message_text = (
            f"Interview Scheduled! "
            f"Job: {job.role} "
            f"Date: {interview.interview_date} "
            f"Mode: {interview.mode} "
            f"For more detail click--/jobseeker/interview/my/"
        )

        if interview.mode == "online":
            message_text += f"Meeting Link: {interview.meeting_link}"
        else:
            message_text += f"Location: {interview.location}"

        Message.objects.create(
            conversation=conversation,
            sender=employer_user,
            text=message_text,
        )