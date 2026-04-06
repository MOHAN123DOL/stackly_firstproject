from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import JobSeeker  
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed  
from .models import Job, UserAppliedJob ,Company , JobSeeker ,JobAlert , JobCategory, ProjectPortfolio
from employees.models import Employee
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import (JobseekerPreference, Skill ,
                     JobseekerPrivacySettings , JobseekerActivityLog ,
                      Jobseekercertificates, JobRecommendationFeedback,ProjectPortfolio , resumetoggle, versioncontrol,Jobseekereducationdetails, 
                      JobExperience ,Jobseekerskills)
from datetime import date
from django.db.models import Count, Q
from datetime import datetime




class JobSeekerAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSeeker
        fields = ['avatar']



class JobSeekerRegistrationSerializer(serializers.Serializer):

    username = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=False, allow_blank=True)


    def validate_username(self, value):
        if len(value) < 4:
            raise serializers.ValidationError("Username must be at least 4 characters.")

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
            if len(value) != 10:
                raise serializers.ValidationError("Phone must be 10 digits.")
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
        password = validated_data.pop("password")
        validated_data.pop("confirm_password")
        phone = validated_data.pop("phone", "")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,
            is_active=True,
        )

        JobSeeker.objects.create(
            user=user,
            phone=phone
        )

        return user




class JobSeekerProfileSerializer(serializers.ModelSerializer):

    welcome = serializers.SerializerMethodField()
    total_experience = serializers.SerializerMethodField()



    class Meta:
        model = JobSeeker
        fields = [
            "welcome",
            "first_name",
            "last_name",
            "title",
         # output
            "total_experience",
            "avatar",
        ]

  


    def get_welcome(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return f"Welcome {request.user.username}"
        return "Welcome"

    def get_total_experience(self, obj):
        from .utils.total_experiences_calculator import calculate_total_experience
    
    
    





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


#for apply jobs

class ApplyJobSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    resume = serializers.FileField(required=False)

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


class ProjectPortfolioSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False,allow_null=True)
    updated_at =  serializers.DateTimeField(read_only = True) 
    created_at = serializers.DateTimeField(read_only = True)
    user_name =  serializers.CharField(source="jobseeker.user.username", read_only = True)
    class Meta:
        model = ProjectPortfolio
        fields = [
                    "id",
                    "user_name",
                    "title",
                    "description",
                    "start_date",
                    "end_date",
                    "is_ongoing",
                    "created_at",
                    "tech_stack",
                    "updated_at",
                    "github_url",
                    "project_url",

                            ]
    
    def validate(self, data):
        request = self.context["request"]
        start = data.get("start_date", self.instance.start_date if self.instance else None)
        end = data.get("end_date", self.instance.end_date if self.instance else None)
        on_going = data.get("is_ongoing", self.instance.is_ongoing if self.instance else False)
        title = data.get("title", self.instance.title if self.instance else None) 
        if on_going and end:
            raise serializers.ValidationError("ongoing project not need end date ")
        if start and end:
            if start > end :
                raise serializers.ValidationError("start date must be lower than end date")
        query=ProjectPortfolio.objects.select_related("jobseeker__user").filter(title=title,jobseeker__user=request.user)
        if self.instance:
            query=query.exclude(id=self.instance.id)
        if query.exists():
            raise serializers.ValidationError("already you have one with same title") 
        return data





class ChatbotMessageSerializer(serializers.Serializer):
    message = serializers.CharField(
        max_length=1000,
        required=True
    )

class JobseekerApplicationStatusSerializer(serializers.ModelSerializer):
    job_role = serializers.CharField(source="job.role", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)

    class Meta:
        model = UserAppliedJob
        fields = [
            "id",
            "job",
            "job_role",
            "company_name",
            "status",
            "applied_at",
        ]
class LandingJobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name")
    company_location = serializers.CharField(source="company.location")
    view_count = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "role",
            "skills",
            "company_name",
            "company_location",
            "min_experience",
            "salary_min",
            "salary_max",
            "duration",
            "view_count",
            "score",
            "application_count",
            "posted_on"
        ]

    def get_view_count(self, obj):
        return getattr(obj, "view_count", 0)

    def get_application_count(self, obj):
        return getattr(obj, "application_count", 0)

    def get_score(self, obj):
        return getattr(obj, "total_score", 0)

    def get_skills(self, obj):
        return [skill.name for skill in obj.skills_required.all()]


class NearbyJobSerializer(LandingJobSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta(LandingJobSerializer.Meta):
        fields = LandingJobSerializer.Meta.fields + ["distance_km"]

    def get_distance_km(self, obj):
        distance = getattr(obj, "distance_km", None)
        if distance is None:
            return None
        return round(float(distance), 2)

class JobseekerPreferenceSerializer(serializers.ModelSerializer):
    preferred_skills = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = JobseekerPreference
        fields = "__all__"
        read_only_fields = ("user",)

    def create(self, validated_data):
        skills = validated_data.pop("preferred_skills", [])
        preference = JobseekerPreference.objects.create(**validated_data)
        preference.preferred_skills.set(skills)
        return preference

    def update(self, instance, validated_data):
        skills = validated_data.pop("preferred_skills", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if skills is not None:
            instance.preferred_skills.set(skills)

        return instance
    

class JobseekerPrivacySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobseekerPrivacySettings
        fields = "__all__"
        read_only_fields = ("user",)




class JobseekerActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobseekerActivityLog
        fields = [
            "id",
            "action_type",
            "description",
            "created_at",
        ]


class JobRecommendationFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRecommendationFeedback
        fields = [
            "id",
            "job",
            "feedback_type",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ("id", "created_at")

class JobseekerDashboardSummarySerializer(serializers.Serializer):
    total_applied_jobs = serializers.IntegerField()
    total_saved_jobs = serializers.IntegerField()
    total_interviews = serializers.IntegerField()
    total_job_alerts = serializers.IntegerField()

    recent_applied_jobs = serializers.ListField()
    recent_saved_jobs = serializers.ListField()

    recommended_jobs = serializers.ListField()

    profile_completion_percentage = serializers.IntegerField()

class resumetoggleserializer(serializers.ModelSerializer):
   
    class Meta:
        model= resumetoggle
        fields =[
            "is_public",
            "is_recruiters_only",
            "is_private",
        ]
    def validate(self, data):
        ispublic = data.get("is_public",self.instance.is_public if self.instance else False)
        Isrecruiters_only =data.get("is_recruiters_only",self.instance.is_recruiters_only if self.instance else False)
        Isprivate = data.get("is_private",self.instance.is_private if self.instance else False)
        if (ispublic and Isrecruiters_only and Isprivate) or (ispublic and Isrecruiters_only) or (ispublic and Isprivate) or(Isprivate and Isrecruiters_only) :
             raise serializers.ValidationError("only one can be true ")  
        if (ispublic or Isrecruiters_only or Isprivate):  
            return data
        else:
            raise serializers.ValidationError("atleast anything will be true") 
        

class resumeversioncontrolserializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    class Meta:
        model=versioncontrol
        fields=[
            "username",
            "version",
            "resumes",
            
        ]

class JobseekerCertificateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Jobseekercertificates
        fields = [
            "certificatetype",
            "certificate",
            "document_name",
            "custom_certificate_name",
            "custom_document_name",
        ]

    def validate(self,data):
        request = self.context["request"]
        EDUCATION_TYPES = ["10TH", "12TH", "DIPLOMA", "UG", "PG"]
        EDUCATION_DOCS = [
        "MARKSHEET", "CONSOLIDATED", "PROVISIONAL",
        "TRANSFER_CERTIFICATE", "BONAFIDE", "DEGREE", "DIPLOMA_CERT"]

        

        certificate_type = data.get("certificatetype") or (self.instance.certificatetype if self.instance else None)
        document_name = data.get("document_name") or (self.instance.document_name if self.instance else None)
        custom_certificate_name = data.get("custom_certificate_name") or (self.instance.custom_certificate_name if self.instance else None)
        custom_document_name = data.get("custom_document_name") or (self.instance.custom_document_name if self.instance else None)
        file = data.get("certificate") or (self.instance.certificate if self.instance else None)
    
        if not certificate_type:
            raise serializers.ValidationError("Certificate type is required")

        if not file:
            raise serializers.ValidationError("File is required")

        if hasattr(file, "size") and file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File must be under 5MB")

        if hasattr(file, "name") and not file.name.endswith((".pdf", ".doc", ".docx")):
            raise serializers.ValidationError("Only PDF/DOC/DOCX allowed")


        if certificate_type in EDUCATION_TYPES:

            if not document_name:
                raise serializers.ValidationError("Document type required")

            if document_name not in EDUCATION_DOCS:
                raise serializers.ValidationError("Invalid education document type")

        elif certificate_type == "SKILL":

            if not custom_certificate_name:
                raise serializers.ValidationError("Skill name required")

            data["document_name"] = "COURSE_COMPLETION"

        elif certificate_type == "PROJECT":

            if not custom_certificate_name:
                raise serializers.ValidationError("Project name required")

            if document_name != "PROJECT_CERT":
                raise serializers.ValidationError("Project must use PROJECT_CERT")
            
        elif certificate_type == "EXPERIENCE":

            if document_name != "EXPERIENCE_LETTER":
                raise serializers.ValidationError("Experience must use EXPERIENCE_LETTER")


        elif certificate_type == "OTHER":

            if not custom_certificate_name:
                raise serializers.ValidationError("Custom certificate name required")

            qs = Jobseekercertificates.objects.filter(
                jobseeker__user=request.user,
                custom_certificate_name=custom_certificate_name
            )

            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError("Certificate name already exists")


        if document_name == "OTHER":

            if not custom_document_name:
                raise serializers.ValidationError("Custom document name required")

            qs = Jobseekercertificates.objects.filter(
                jobseeker__user=request.user,
                custom_document_name=custom_document_name
            )

            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError("Document name already exists")
            
        queryset = Jobseekercertificates.objects.filter(
            jobseeker__user=request.user,
            certificatetype=certificate_type
        )

        if certificate_type in ["SKILL", "PROJECT"]:
            queryset = queryset.filter(
                custom_certificate_name=custom_certificate_name
            )

            queryset = queryset.filter(
                document_name=document_name
            )

        elif certificate_type == "EXPERIENCE":
            queryset = queryset.filter(
                document_name="EXPERIENCE_LETTER"
            )
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError("Duplicate certificate already exists")

        return data
    

class JobseekerEducationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model= Jobseekereducationdetails
        fields = [
            "education_type",
            "school_name",
            "college_name",
            "start_date",
            "end_date",
            "percentage",
            "studying",
            "history_of_backlog",
        ]
    def validate(self,data):
        request = self.context["request"]
        EDUCATION_TYPES = ["10TH", "12TH"]
        EDUCATION_ORDER = {
                "10TH": 1,
                "12TH": 2,
                "DIPLOMA": 2,
                "UG": 3,
                "PG": 4
            }
        education_type=data.get("education_type") or (self.instance.education_type if self.instance else None)
        school_name = data.get("school_name") or (self.instance.school_name if self.instance else None)
        college_name = data.get("college_name") or (self.instance.college_name if self.instance else None)
        start_date =  data.get("start_date") or (self.instance.start_date if self.instance else None)
        end_date =  data.get("end_date") or (self.instance.end_date if self.instance else None)
        percentage = data.get("percentage") or (self.instance.percentage if self.instance else None) 
        studying = data.get("studying") or (self.instance.studying if self.instance else None)
        if not education_type:
            raise serializers.ValidationError("education type cannot be none")
        if education_type in EDUCATION_TYPES:
            if not school_name:
                raise serializers.ValidationError("school  name needed")
            data["college_name"] = None
        if education_type not in EDUCATION_TYPES:
            if not college_name:
                raise serializers.ValidationError(" college name needed")
            data["school_name"] = None
        if not start_date:
             raise serializers.ValidationError("start date cannot be none")
        if not end_date:
             if not studying:
                raise serializers.ValidationError("end date  or studying any field required")
        if studying:
            qss = Jobseekereducationdetails.objects.filter(
            jobseeker__user=request.user,
            studying=True)
            if self.instance:
                qss=qss.exclude(id=self.instance.id)
            if qss.exists():
                raise serializers.ValidationError("already you are studying another education ")
        if end_date:
            if (start_date > end_date):
             raise serializers.ValidationError("start data is higher than end date")
            if not percentage:
                raise serializers.ValidationError("percentage required")

        
        queryset = Jobseekereducationdetails.objects.filter(
            jobseeker__user=request.user,
            education_type=education_type)
        if self.instance:
            queryset=queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("education details already exists")
        
        existing_studying = Jobseekereducationdetails.objects.filter(
        jobseeker__user=request.user,
        studying=True)
        current_order = EDUCATION_ORDER.get(education_type)
        if self.instance:
            existing_studying = existing_studying.exclude(id=self.instance.id)
        if existing_studying.exists():
            studying_record = existing_studying.first()
            studying_order = EDUCATION_ORDER.get(studying_record.education_type)
            if current_order > studying_order:
                raise serializers.ValidationError(
                    f"You cannot add {education_type} while studying {studying_record.education_type}"
                )

        qs = Jobseekereducationdetails.objects.filter(
            jobseeker__user=request.user
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        for edu in qs:
            existing_order = EDUCATION_ORDER.get(edu.education_type)

            if current_order == existing_order:
                if edu.end_date and end_date:
                    if start_date <= edu.end_date and end_date >= edu.start_date:
                        raise serializers.ValidationError(
                            f"{education_type} overlaps with existing {edu.education_type}"
                        )

            elif current_order > existing_order:
                if edu.end_date and start_date <= edu.end_date:
                    raise serializers.ValidationError(
                        f"{education_type} must start after {edu.education_type} ends"
                    )
            
            elif current_order < existing_order:
                if end_date and end_date >= edu.start_date:
                    raise serializers.ValidationError(
                        f"{education_type} must end before {edu.education_type} starts"
                    )

        return data
    

class JobseekerExperienceSerializers(serializers.ModelSerializer):
    class Meta:
        model = JobExperience
        fields = [
            "company_name",
            "start_date",
            "end_date",
            "is_current",
            "uuid"
            
        ]
    def validate(self, data):
        today = date.today()
        request = self.context["request"]
        Company_name = data.get("company_name") or (self.instance.company_name if self.instance else None)
        start_date = data.get("start_date") or (self.instance.start_date if self.instance else None)
        end_date = data.get("end_date") or (self.instance.end_date if self.instance else None)
        is_current = data.get("is_current") or (self.instance.is_current if self.instance else False)   
        if not Company_name:
            raise serializers.ValidationError("company name required")
        if not start_date :
            raise serializers.ValidationError("start data is needed")
        if not is_current:
            if not end_date:
                raise serializers.ValidationError("end date required")
        if start_date > today:
            raise serializers.ValidationError("Start date cannot be in the future")

        if end_date and end_date > today:
            raise serializers.ValidationError("End date cannot be in the future")

        if start_date and end_date :
            if start_date > end_date:
                raise serializers.ValidationError("end date will be high")  
            
        if not is_current:
            if not end_date:
                raise serializers.ValidationError("End date is required")
        else:
            end_date = end_date or start_date

        qs = JobExperience.objects.filter(jobseeker__user=request.user)

        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if start_date and end_date:
            overlap = qs.filter(
                Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
            ).exists()

            if overlap:
                raise serializers.ValidationError("Experience dates overlap with existing record")
    

        return data
    


class JobseekerSkillsSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )

    skills_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Jobseekerskills
        fields = ["skills", "skills_list"]

    def get_skills_list(self, obj):
        return [skill.name for skill in obj.skills.all()]

    def validate_skills(self, value):
        return list(set([skill.strip().lower() for skill in value]))

    def create_or_update_skills(self, instance, skills_data):
        skill_objs = []

        for skill_name in skills_data:
            skill_obj = Skill.objects.filter(name__iexact=skill_name).first()

            if not skill_obj:
                skill_obj = Skill.objects.create(name=skill_name.title())
            skill_objs.append(skill_obj)

        instance.skills.add(*skill_objs)  
    def create(self, validated_data):
        skills_data = validated_data.pop("skills", [])
        request = self.context["request"]

        jobseeker, _ = JobSeeker.objects.get_or_create(user=request.user)
        obj, _ = Jobseekerskills.objects.get_or_create(jobseeker=jobseeker)

        self.create_or_update_skills(obj, skills_data)

        return obj
  
    def update(self, instance, validated_data):
        skills_data = validated_data.get("skills")

        if skills_data is not None:
            self.create_or_update_skills(instance, skills_data)

        return instance
        
                