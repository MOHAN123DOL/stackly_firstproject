from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode , urlsafe_base64_decode
from django.utils.encoding import force_bytes , force_str
from .serializers import EmployerForgotPasswordSerializer , EmployeeRegistrationSerializer

from .serializers import ResetPasswordConfirmSerializer

import random
from .models import PasswordResetOTP
from .serializers import EmployerForgotPasswordOTPSerializer

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



import random
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

from .models import PasswordResetOTP
from .serializers import EmployerForgotPasswordOTPSerializer


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

        # TEMP: print OTP (replace with email later)
        print("PASSWORD RESET OTP:", otp)

        return Response(
            {"message": "OTP sent to your email"},
            status=status.HTTP_200_OK
        )

from django.utils.timezone import now
from .serializers import ResetPasswordWithOTPSerializer


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

        # Cleanup OTPs
        PasswordResetOTP.objects.filter(user=user).delete()

        return Response(
            {"message": "Password reset successful. Please login."},
            status=status.HTTP_200_OK
        )
