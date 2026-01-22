from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.images import get_image_dimensions
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import JobSeeker
from .serializers import (
    JobSeekerAvatarSerializer,
    JobSeekerRegistrationSerializer,
    CustomTokenSerializer,
    ChangePasswordSerializer,
    JobSeekerProfileSerializer,
)
from notifications.utils import create_notification


def test_avatar(request):
    return render(request, "jobseeker/avatar_upload.html")


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
    serializer_class = JobSeekerRegistrationSerializer
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
                "login_url": "/api/login/",
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
