from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Employee
from jobseeker.models import Job


#FOR SIGNUP PAGE 

class EmployeeRegistrationSerializer(serializers.ModelSerializer):

    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True,style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True,style={"input_type": "password"})

    class Meta:
        model = Employee
        fields = [
            "username",
            "email",
            "company_name",
            "password",
            "confirm_password",
        ]

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}
            )

        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "Username already exists"}
            )

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "Email already exists"}
            )

        return data

    def create(self, validated_data):
        username = validated_data.pop("username")
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        validated_data.pop("confirm_password")

        # 🔹 Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True  # Employee flag
        )

        # 🔹 Create Employee profile
        employee = Employee.objects.create(
            user=user,
            **validated_data
        )

        return employee

#FOR FORGOT PASSWORD AND GET TOKEN LINK AND ALLOW USER CREATE NEW PASSWORD

class EmployerForgotPasswordOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = User.objects.filter(email=value, is_staff=True).first()
        if not user:
            raise serializers.ValidationError("Employer not found")
        return value

class ResetPasswordWithOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}
            )
        return data



class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "company",
            "role",
            "salary_min",
            "salary_max",
            "duration",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        salary_min = data.get("salary_min")
        salary_max = data.get("salary_max")

        # salary must start from 2 LPA
        if salary_min is not None and salary_min < 2:
            raise serializers.ValidationError(
                {"salary_min": "Minimum salary must be at least 2 LPA."}
            )

        if salary_max is not None and salary_max < 2:
            raise serializers.ValidationError(
                {"salary_max": "Maximum salary must be at least 2 LPA."}
            )

        if salary_min and salary_max and salary_max < salary_min:
            raise serializers.ValidationError(
                {"salary_max": "Maximum salary must be greater than or equal to minimum salary."}
            )

        return data
