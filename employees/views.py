from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .serializers import EmployerForgotPasswordSerializer , EmployeeRegistrationSerializer


class EmployerForgotPasswordAPI(GenericAPIView):
    serializer_class = EmployerForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email, is_staff=True)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        reset_link = f"http://frontend-url/employer/reset-password/{uid}/{token}/"
        print("Employer Reset Link:", reset_link)

        return Response(
            {"message": "Password reset link sent to your email"},
            status=status.HTTP_200_OK
        )



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

