from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import JobSeeker  
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed  
from .models import Job, UserAppliedJob ,Company , JobSeeker ,JobAlert , JobCategory
from employees.models import Employee

class JobSeekerAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSeeker
        fields = ['avatar']




class UserRegistrationSerializer(serializers.Serializer):
    ROLE_CHOICES = (
        ("jobseeker", "Job Seeker"),
    )

    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ROLE_CHOICES)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

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
        role = validated_data.pop("role")

        user = User(
            username=validated_data["username"],
            email=validated_data.get("email"),
        )

        user.set_password(validated_data["password"])
        user.save()

        # 🔹 Create profile based on role
        if role == "jobseeker":
            JobSeeker.objects.create(user=user)
        

        return user



class JobSeekerProfileSerializer(serializers.ModelSerializer):
    welcome = serializers.SerializerMethodField()

    class Meta:
        model = JobSeeker
        fields = [
            "welcome",
            "first_name",
            "last_name",
            "education",
            "title",
            "total_experience",
            "avatar",
        ]

    def get_welcome(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return f"Welcome {request.user.username}"
        return "Welcome"







class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("New passwords do not match")
        return data


class CustomTokenSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        login_value = attrs.get("username")
        password = attrs.get("password")

        # 🔹 Allow login with email or username
        if "@" in login_value:
            user = User.objects.filter(email__iexact=login_value).first()
            if not user:
                raise AuthenticationFailed("Invalid email or password")
            username = user.username
        else:
            username = login_value

        # 🔹 Authenticate user
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed("Invalid username/email or password")

        self.user = user

        # 🔹 Generate JWT tokens
        data = super().validate({
            "username": username,
            "password": password
        })

        # 🔹 Role-based response
        if user.is_staff:
            data["role"] = "employer"
            data["message"] = f"Welcome Employer {user.username}"
            data["redirect_url"] = "/employer/dashboard/"
        else:
            data["role"] = "jobseeker"
            data["message"] = f"Welcome {user.username}"
            data["redirect_url"] = "/jobseeker/dashboard/"

        data["username"] = user.username

        return data




class CompanyJobSerializer(serializers.ModelSerializer):
    applied_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Job
        fields = [
            "id",
            "role",
            "salary",
            "duration",
            "posted_on",
            "applied_count",
        ]



class CompanyLogoUploadSerializer(serializers.Serializer):
    company_logo = serializers.ImageField()



class OpportunityCompanySerializer(serializers.ModelSerializer):
    company_logo = serializers.ImageField(use_url=True)
    jobs_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "company_logo",
            "location",
            "jobs_count",
        ]


class LandingJobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_location = serializers.CharField(source="company.location", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "role",
            "company_name",
            "company_location",
            "salary_min",
            "salary_max",
            "duration",
            "posted_on",
        ]
#for apply jobs

class ApplyJobSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()

#FOR CREATE JOBALERT IF ROLE NOT ENTERED WE NEED TO TAKE FROM PROFILE TITLE

class JobAlertSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get("role"):
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                try:
                    jobseeker = JobSeeker.objects.get(user=request.user)
                    if jobseeker.title:
                        data["role"] = jobseeker.title
                except JobSeeker.DoesNotExist:
                    pass

        
        if not data.get("role"):
            raise serializers.ValidationError({
                "role": "Role is required or JobSeeker title must exist."
            })

        return data

    class Meta:
        model = JobAlert
        fields = [
            "id",
            "role",
            "locations",
            "duration",
            "min_salary",
            "max_salary",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class JobCategoryListSerializer(serializers.ModelSerializer):
    jobs_count = serializers.IntegerField(read_only=True)
    user = serializers.IntegerField(read_only=True)
    class Meta:
        model = JobCategory
        fields = [
            "id",
            "name",
            "is_active",
            "created_at",
            "jobs_count",
            "user"
        ]
        read_only_fields = ["id", "created_at"]


class JobcatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "role",
            "salary_min",
            "salary_max",
            "duration",
            "posted_on",
        ]

class ResumeUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSeeker
        fields = ["resume"]

    def validate_resume(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume size must be under 5MB.")

        if not value.name.endswith((".pdf", ".doc", ".docx")):
            raise serializers.ValidationError("Only PDF or DOC files are allowed.")

        return value


class ChatbotMessageSerializer(serializers.Serializer):
    message = serializers.CharField(
        max_length=1000,
        required=True
    )