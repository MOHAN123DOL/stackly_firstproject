from rest_framework.generics import GenericAPIView ,CreateAPIView , ListAPIView ,RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User 
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from jobseeker.models import Job , JobCategory
import random
from .models import PasswordResetOTP
from django.utils.timezone import now
from .serializers import (ResetPasswordWithOTPSerializer , JobCategorySerializer 
                          , EmployeeRegistrationSerializer ,EmployerForgotPasswordOTPSerializer ,JobCreateSerializer, )
from django.db.models import Count
from rest_framework.views import APIView
#FOR SIGNUP PAGE 

class EmployeeRegistrationAPI(GenericAPIView):
    serializer_class = EmployeeRegistrationSerializer
    permission_classes = []  

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Employee registration successful. Please login.",
                "login_url": "employee/login/all",
            },
            status=status.HTTP_201_CREATED
        )


#FOR FORGOT PASSWORD AND GET TOKEN LINK AND ALLOW USER CREATE NEW PASSWORD

class EmployerForgotPasswordOTPAPI(GenericAPIView):
    serializer_class = EmployerForgotPasswordOTPSerializer
    permission_classes = []
    authentication_classes = []

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


