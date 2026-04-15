from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Employee , Interview
from jobseeker.models import Job , JobCategory , UserAppliedJob
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from jobseeker.models import JobSeeker
from django.utils import timezone

class EmployeeRegistrationSerializer(serializers.ModelSerializer):

    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    company_name = serializers.CharField(write_only=True)

    class Meta:
        model = Employee
        fields = [
            "username",
            "email",
            "company_name",
            "designation",
            "phone",
            "password",
            "confirm_password",
        ]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_phone(self, value):
        if value:
            if not value.isdigit():
                raise serializers.ValidationError("Phone must contain only digits.")
            if len(value) < 10:
                raise serializers.ValidationError("Phone must be at least 10 digits.")
        return value

  

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        validate_password(attrs["password"])  
        return attrs

 

    @transaction.atomic
    def create(self, validated_data):

        company_name = validated_data.pop("company_name").strip()
        username = validated_data.pop("username")
        email = validated_data.pop("email").lower()
        password = validated_data.pop("password")
        validated_data.pop("confirm_password")

        # Create or get company
        company, created = Company.objects.get_or_create(name=company_name)

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=True,
            is_staff = True,
        )

        # First employee = owner
        if created:
            role = "owner"
            
        else :
             role = "recruiter"
             
    
        
        employee = Employee.objects.create(
            user=user,
            company=company,
            role=role,
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
    category = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.filter(is_active=True)
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "company",
            "category",       
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



class JobCategorySerializer(serializers.ModelSerializer):
    jobs_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = JobCategory
        fields = [
            "id",
            "name",
            "is_active",
            "created_at",
            "jobs_count"
        ]
        read_only_fields = ["id", "created_at"]
class InterviewSerializer(serializers.ModelSerializer):

    interview_date = serializers.DateTimeField(
        
    )

    scheduled_by = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    reminder_sent_1hr = serializers.BooleanField(read_only=True)

    class Meta:
        model = Interview
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        company_id = self.context.get("company_id")

        if request and request.user.is_authenticated and company_id:
            self.fields["job"].queryset = Job.objects.filter(
                company_id=company_id
            ).select_related("company").only("id", "role", "company_id", "company__name")

            self.fields["jobseeker"].queryset = JobSeeker.objects.filter(
                user__userappliedjob__job__company_id=company_id
            ).select_related("user").only("id", "user_id", "user__username").distinct()
        else:
            self.fields["job"].queryset = Job.objects.none()
            self.fields["jobseeker"].queryset = JobSeeker.objects.none()

    
    def validate_interview_date(self, value):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value

   
    def validate(self, data):
        mode = data.get("mode")
        meeting_link = data.get("meeting_link")
        location = data.get("location")

        if mode == "online":
            if not meeting_link:
                raise serializers.ValidationError(
                    "Meeting link is required for online interviews."
                )
            data["location"] = None

        elif mode == "offline":
            if not location:
                raise serializers.ValidationError(
                    "Location is required for offline interviews."
                )
            data["meeting_link"] = None

        else:
            raise serializers.ValidationError(
                "Mode must be either 'online' or 'offline'."
            )

        return data

class EmployerApplicationListSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(source="user.jobseeker.first_name", read_only=True)
    last_name = serializers.CharField(source="user.jobseeker.last_name", read_only=True)
    phone = serializers.CharField(source="user.jobseeker.phone", read_only=True)
    title = serializers.CharField(source="user.jobseeker.title", read_only=True)
    education = serializers.CharField(source="user.jobseeker.education", read_only=True)
    user_name = serializers.CharField(
        source="user.username",
        read_only=True
    )
    resume = serializers.SerializerMethodField()

    class Meta:
        model = UserAppliedJob
        fields = [
            "id",
            "user",
            "user_name",
            "first_name",
            "last_name",
            "phone",
            "title",
            "education",
            "resume",
            "status",
            "applied_at"
        ]

    def get_resume(self, obj):
      #get applied job resume 

        if obj.resume:
            return obj.resume.url

     #get or get from jobseeker

        if hasattr(obj.user, "jobseeker") and obj.user.jobseeker.resume:
            return obj.user.jobseeker.resume.url

        return None
    
class EmployerUpdateStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAppliedJob
        fields = ["status"]
