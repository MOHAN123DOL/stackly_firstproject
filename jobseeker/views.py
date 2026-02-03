from rest_framework.generics import GenericAPIView , ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.images import get_image_dimensions
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import BasePermission
from .models import JobSeeker , UserAppliedJob, UserSavedJob ,Company, Job 
from .serializers import (
    JobSeekerAvatarSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    JobSeekerProfileSerializer,
    CustomTokenSerializer,
    CompanyJobSerializer,
    CompanyLogoUploadSerializer,
    OpportunityCompanySerializer,
   
    
)
from notifications.utils import create_notification
from notifications.models import Notification
from django.utils.timezone import now
from datetime import timedelta
from rest_framework.views import APIView
from django.db.models import Count
from django.contrib.auth.models import User
from employees.models import Employee
from .services import get_opportunities_overview


class JobSeekerAvatarAPI(GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = JobSeekerAvatarSerializer

    def _check_jobseeker_access(self, request):
        if request.user.is_superuser:
            return Response(
                {"error": "Superuser not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def _get_jobseeker(self, request):
        return JobSeeker.objects.get_or_create(user=request.user)[0]

    def get(self, request):
        error = self._check_jobseeker_access(request)
        if error:
            return error

        jobseeker = self._get_jobseeker(request)
        serializer = self.get_serializer(jobseeker)
        return Response(serializer.data)

    def post(self, request):
        error = self._check_jobseeker_access(request)
        if error:
            return error

        jobseeker = self._get_jobseeker(request)

        if 'avatar' not in request.FILES:
            return Response(
                {"error": "Avatar file is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        avatar = request.FILES['avatar']

        if avatar.size > 2 * 1024 * 1024:
            return Response(
                {"error": "Maximum file size is 2MB"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            get_image_dimensions(avatar)
        except Exception:
            return Response(
                {"error": "Only image files are allowed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            jobseeker,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        create_notification(request.user, "Avatar updated successfully")
        return Response(
            {"message": "Avatar uploaded successfully", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        jobseeker = self._get_jobseeker(request)

        if not jobseeker.avatar:
            return Response(
                {"error": "No avatar to delete"},
                status=status.HTTP_400_BAD_REQUEST
            )

        jobseeker.avatar.delete(save=False)
        jobseeker.avatar = None
        jobseeker.save()

        create_notification(request.user, "Avatar removed")

        return Response(
            {"message": "Avatar deleted successfully"},
            status=status.HTTP_200_OK
        )


class JobSeekerRegistrationAPI(GenericAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        
        user = serializer.save()

        create_notification(user, "Registration completed successfully")

        return Response(
            {
                "message": "Registration successful. Please login.",
                "login_url": "jobseeker/login/all",
            },
            status=status.HTTP_201_CREATED,
        )


class CustomLoginAPI(TokenObtainPairView):
    serializer_class = CustomTokenSerializer



class JobSeekerProfileAPI(GenericAPIView):
    serializer_class = JobSeekerProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        jobseeker, _ = JobSeeker.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(jobseeker)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        jobseeker, _ = JobSeeker.objects.get_or_create(user=request.user)

        serializer = self.get_serializer(jobseeker, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        create_notification(request.user, "Profile updated successfully")
        return Response(serializer.data)


class ChangePasswordAPI(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        create_notification(user, "Password changed successfully")

        return Response(
            {"message": f"{user.username} Your Password changed successfully"},
            status=status.HTTP_200_OK,
        )
    
class JobSeekerDashboardCountAPI(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1️⃣ Notifications count
        total_notifications = Notification.objects.filter(
            user=user
        ).count()

        unread_notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()

        # 2️⃣ JobSeeker profile (ensure exists)
        jobseeker, _ = JobSeeker.objects.get_or_create(user=user)

        fields = [
            bool(jobseeker.avatar),
            bool(jobseeker.first_name.strip()),
            bool(jobseeker.last_name.strip()),
            bool(jobseeker.education.strip()),
            bool(jobseeker.experience.strip()),
        ]

        completed_fields = sum(fields)
        total_fields = len(fields)

        profile_completion = int(
            (completed_fields / total_fields) * 100
        )
        applied_job=UserAppliedJob.objects.filter(user=user).count()
        saved_job=UserSavedJob.objects.filter(user=user).count()

        jobseeker = JobSeeker.objects.get(user=user)

        yesterday = now().date() - timedelta(days=1)
        if jobseeker.updated_at.date() == yesterday or jobseeker.updated_at.date() == now().date():
            is_daily_followup = True
        else :
            is_daily_followup = False

        return Response(
            {
                "notifications": total_notifications,
                "unread_notifications": unread_notifications,
                "profile_completion": f"{profile_completion}%",
                "Applied_Job" : applied_job,
                "Saved_Job" : saved_job,
                "is_user_daily_active" :  is_daily_followup
            },
            status=status.HTTP_200_OK
        )



class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.user.username
        return Response(
            {"message": f"{username} Logout successfully",
            "login_link":"/api/login/" },
            status=status.HTTP_200_OK
        )




class CompanyJobsAPI(APIView):

    def get(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        jobs = (
            Job.objects
            .filter(company=company)
            .annotate(applied_count=Count("userappliedjob"))
            .order_by("-posted_on")
        )

        serializer = CompanyJobSerializer(jobs, many=True)

        return Response(
            {
                "company_id": company.id,
                "company_name": company.name,
                "total_jobs": jobs.count(),

                "jobs": serializer.data
            },
            status=status.HTTP_200_OK
        )




class CompanyLogoUploadAPI(GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = CompanyLogoUploadSerializer

    def post(self, request, company_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        company.company_logo = serializer.validated_data["company_logo"]
        company.save(update_fields=["company_logo"])
        
        return Response(
            {"message": "Company logo uploaded successfully"},
            status=status.HTTP_200_OK
        )


class JobSeekerOpportunitiesCompanyListAPI(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OpportunityCompanySerializer

    def get_queryset(self):
        return (
            Company.objects
            .annotate(jobs_count=Count("jobs"))
            .order_by("-created_at")
        )



class JobSeekerOpportunitiesOverviewAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            return Response(
                {"error": "Employers cannot access this page"},
                status=403
            )

        data = get_opportunities_overview(request.user)
        return Response(data, status=200)
