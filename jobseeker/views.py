from rest_framework.generics import GenericAPIView , ListAPIView , CreateAPIView , RetrieveUpdateDestroyAPIView, ListCreateAPIView 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.images import get_image_dimensions
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.paginator import EmptyPage
from django.core.cache import cache
from django.db.models import Count, Q
from .models import (JobSeeker , UserAppliedJob, UserSavedJob ,Company, 
Job , JobAlert , JobCategory , Skill , JobView , JobseekerPrivacySettings , 
JobseekerActivityLog, JobRecommendationFeedback, ProjectPortfolio , resumetoggle, versioncontrol , Jobseekercertificates,Jobseekereducationdetails,JobExperience, Jobseekerskills)
from .utils.version_history_resume import createversionccontrolresume
from .serializers import (
    JobSeekerAvatarSerializer,
    JobSeekerRegistrationSerializer,
    ChangePasswordSerializer,
    JobSeekerProfileSerializer,
    CustomTokenSerializer,
    CompanyJobSerializer,
    CompanyLogoUploadSerializer,
    OpportunityCompanySerializer,
    ApplyJobSerializer,
    JobAlertSerializer,
    JobcatSerializer,
    JobCategoryListSerializer,
    ChatbotMessageSerializer,
    JobseekerApplicationStatusSerializer,
    LandingJobSerializer,
    NearbyJobSerializer,
    JobseekerPrivacySettingsSerializer,
    JobseekerActivityLogSerializer,
    JobRecommendationFeedbackSerializer,
    ProjectPortfolioSerializer,
    resumetoggleserializer,
    resumeversioncontrolserializer,
    JobseekerCertificateSerializer,
    JobseekerEducationDetailsSerializer,
    JobseekerExperienceSerializers,
   
   )
from .models import JobSeeker, Jobseekerskills
from .serializers import JobseekerSkillsSerializer

from rest_framework.generics import RetrieveUpdateAPIView
from .models import JobseekerPreference
from .serializers import JobseekerPreferenceSerializer
from employees.serializers import InterviewSerializer
from .models import UnansweredQuestion
from .services import ask_ai , find_best_answer , create_activity_log , AdvancedProfileStrengthService , NearbyJobService
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from notifications.utils import create_notification
from notifications.models import Notification
from django.utils.timezone import now
from datetime import timedelta
from math import atan2, cos, radians, sin, sqrt
from rest_framework.views import APIView
from django.db.models import Count
from django.contrib.auth.models import User
from employees.models import Employee , Interview
from .services import get_opportunities_overview , AdvancedWeeklyJobMatchService
from .pagination import LandingJobPagination
from .utils.Matching import match_jobs
from .serializers import ResumeUploadSerializer
from.utils.resume_apyhub import parse_resume_with_rapidapi 
from datetime import date
from.utils.total_experiences_calculator import calculate_total_experience
from .utils.profile_completion_percentage import calculate_profile_completion
from .utils.job_reccomedation import generate_recommendations
from .utils.jobseeker_engagement_score import calculate_engagement_score


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
#-----------------------------------------------------------------------------
        create_notification(request.user, "Avatar updated successfully")
        create_activity_log(
    request.user,
    "UPDATED_AVATAR",
    "updated profile picture")
#-------------------------------------------------------------------------------
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
#---------------------------------------------------------------
        create_notification(request.user, "Avatar removed")
        create_activity_log(
    request.user,
    "REMOVED_AVATAR",
    "removed profile picture"
)
#---------------------------------------------------------------
        return Response(
            {"message": "Avatar deleted successfully"},
            status=status.HTTP_200_OK
        )


class JobSeekerRegistrationAPI(CreateAPIView):

    serializer_class = JobSeekerRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
#-------------------------------------------------------------------------------------------
        create_notification(user, "Registration completed successfully")
#------------------------------------------------------------------------------------
        return Response(
            {
                "success": True,
                "message": "Registration successful. Please login.",
                "data": {
                    "username": user.username,
                    "email": user.email,
                }
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
        jobseeker, _ = JobSeeker.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(jobseeker)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def patch(self, request):
        jobseeker, _ = JobSeeker.objects.get_or_create(
            user=request.user
        )

        serializer = self.get_serializer(
            jobseeker,
            data=request.data,
            partial=True   
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
#----------------------------------------------------------------
        create_notification(
            request.user,
            "Profile updated successfully"
        )
        create_activity_log(
    request.user,
    "UPDATED_PROFILE", "Updated Profile"
)
#----------------------------------------------------------------------

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )





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
#----------------------------------------------------------------------------------------
        create_notification(user, "Password changed successfully")
        create_activity_log(
    request.user,
    "UPDATED_PASSWORD", "password changed"
)
#-------------------------------------------------------------------------------------

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
             bool(jobseeker.first_name),
            bool(jobseeker.last_name),
            bool(jobseeker.education),
            bool(jobseeker.title),
            bool(jobseeker.avatar),
            bool(jobseeker.resume),
            jobseeker.skills.exists(),
            jobseeker.experiences.exists(),
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




class LandingJobListingAPI(APIView):
    permission_classes = [AllowAny]
    pagination_class = LandingJobPagination

    def _parse_int_param(self, value, field_name):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError({field_name: "Must be a valid integer."})

    def _build_remote_filter(self, remote_value):
        if remote_value in (None, ""):
            return None

        value = remote_value.strip().lower()
        remote_terms = (
            Q(company__location__icontains="remote")
            | Q(company__location__icontains="work from home")
            | Q(company__location__icontains="wfh")
        )
        hybrid_terms = Q(company__location__icontains="hybrid")

        if value in {"true", "1", "yes", "remote"}:
            return ("filter", remote_terms)
        if value in {"false", "0", "no", "onsite", "on-site"}:
            return ("exclude", remote_terms | hybrid_terms)
        if value == "hybrid":
            return ("filter", hybrid_terms)

        raise ValidationError(
            {"remote": "Use one of: true, false, hybrid, remote, onsite."}
        )

    def get(self, request):
        qs = (
            Job.objects.select_related("company")
            .prefetch_related("skills_required")
            .annotate(
                view_count=Count("views", distinct=True),
                application_count=Count("applications", distinct=True),
            )
        )

        role = request.GET.get("role")
        company = request.GET.get("company")
        locations = request.GET.get("location")
        durations = request.GET.get("duration")
        skills = request.GET.get("skills")
        skills_match = request.GET.get("skills_match", "any").strip().lower()
        remote_value = request.GET.get("remote")

        salary_min = self._parse_int_param(request.GET.get("salary_min"), "salary_min")
        salary_max = self._parse_int_param(request.GET.get("salary_max"), "salary_max")
        experience = self._parse_int_param(request.GET.get("experience"), "experience")
        experience_min = self._parse_int_param(request.GET.get("experience_min"), "experience_min")
        experience_max = self._parse_int_param(request.GET.get("experience_max"), "experience_max")

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise ValidationError(
                {"salary_range": "salary_min must be less than or equal to salary_max."}
            )

        if experience is not None and (
            experience_min is not None or experience_max is not None
        ):
            raise ValidationError(
                {"experience": "Use either experience or experience_min/experience_max, not both."}
            )

        if (
            experience_min is not None
            and experience_max is not None
            and experience_min > experience_max
        ):
            raise ValidationError(
                {
                    "experience_range": (
                        "experience_min must be less than or equal to experience_max."
                    )
                }
            )

        if role:
            qs = qs.filter(role__icontains=role.strip())

        if company:
            company_query = Q()
            company_list = [item.strip() for item in company.split(",") if item.strip()]
            for company_name in company_list:
                company_query |= Q(company__name__iexact=company_name)
            if company_query:
                qs = qs.filter(company_query)

        if locations:
            location_query = Q()
            location_list = [item.strip() for item in locations.split(",") if item.strip()]
            for location in location_list:
                location_query |= Q(company__location__icontains=location)
            if location_query:
                qs = qs.filter(location_query)

        if durations:
            duration_query = Q()
            duration_list = [item.strip() for item in durations.split(",") if item.strip()]
            for duration in duration_list:
                duration_query |= Q(duration__iexact=duration)
            if duration_query:
                qs = qs.filter(duration_query)

        if salary_min is not None:
            qs = qs.filter(Q(salary_max__gte=salary_min) | Q(salary_max__isnull=True))

        if salary_max is not None:
            qs = qs.filter(Q(salary_min__lte=salary_max) | Q(salary_min__isnull=True))

        if experience is not None:
            qs = qs.filter(Q(min_experience__lte=experience) | Q(min_experience__isnull=True))

        if experience_min is not None:
            qs = qs.filter(min_experience__gte=experience_min)

        if experience_max is not None:
            qs = qs.filter(Q(min_experience__lte=experience_max) | Q(min_experience__isnull=True))

        remote_filter = self._build_remote_filter(remote_value)
        if remote_filter:
            mode, condition = remote_filter
            if mode == "filter":
                qs = qs.filter(condition)
            else:
                qs = qs.exclude(condition)

        if skills:
            skill_names = [item.strip() for item in skills.split(",") if item.strip()]
            if not skill_names:
                raise ValidationError({"skills": "Provide at least one valid skill."})

            if skills_match not in {"any", "all"}:
                raise ValidationError({"skills_match": "Use either 'any' or 'all'."})

            if skills_match == "all":
                for skill in skill_names:
                    qs = qs.filter(skills_required__name__iexact=skill)
            else:
                skill_query = Q()
                for skill in skill_names:
                    skill_query |= Q(skills_required__name__iexact=skill)
                qs = qs.filter(skill_query)

        qs = qs.distinct().order_by("-posted_on")

        paginator = self.pagination_class()

        try:
            page = paginator.paginate_queryset(qs, request)
        except EmptyPage:
            request.GET._mutable = True
            request.GET['page'] = 1
            page = paginator.paginate_queryset(qs, request)

        serializer = LandingJobSerializer(page, many=True)

        return paginator.get_paginated_response({
            "total_jobs": paginator.page.paginator.count,
            "jobs": serializer.data
        })


#for apply job
class ApplyJobAPIView(CreateAPIView):
    serializer_class = ApplyJobSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(
            Job,
            id=serializer.validated_data["job_id"]
        )

        # Prevent duplicate application
        if UserAppliedJob.objects.filter(
            user=request.user,
            job=job
        ).exists():
            raise ValidationError({"detail": "Already applied"})

        # Get jobseeker profile
        try:
            jobseeker_profile = request.user.jobseeker
        except:
            raise ValidationError({"detail": "Jobseeker profile not found"})

        uploaded_resume = serializer.validated_data.get("resume")

        # Resume validation logic
        if not uploaded_resume and not jobseeker_profile.resume:
            raise ValidationError({
                "detail": "Upload resume in profile or while applying."
            })

        resume_to_save = uploaded_resume or jobseeker_profile.resume

        application = UserAppliedJob.objects.create(
            user=request.user,
            job=job,
            resume=resume_to_save
        )
        create_activity_log(
            request.user,
            "APPLIED_JOB",
            f"Applied for {job.role} at {job.company.name}"
        )

        return Response({
            "message": "Job applied successfully",
            "job_id": application.job.id,
            "job_name": application.job.role,
            "company": application.job.company.name,
            "resume_uploaded": bool(application.resume),
            "status": application.status
        }, status=201)


#for job alert crud 
class JobAlertCreateAPIView(CreateAPIView):
    serializer_class = JobAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        # pass request to serializer (needed for auto-fill role)
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        # user is always taken from token/session, not from payload
        serializer.save(user=self.request.user)

class JobAlertListAPIView(ListAPIView):
    serializer_class = JobAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobAlert.objects.filter(user=self.request.user).order_by("-created_at")



class JobAlertDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = JobAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # user-scoped queryset = security
        return JobAlert.objects.filter(user=self.request.user)
    
    
#for match and new alert

class JobAlertMatchesAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LandingJobSerializer

    def get(self, request, alert_id):
        alert = get_object_or_404(
            JobAlert,
            id=alert_id,
            user=request.user,
            is_active=True
        )
        jobs = match_jobs(alert)

        # user has now READ the alert
        alert.last_read_at = now()
        alert.save(update_fields=["last_read_at"])

        serializer = self.get_serializer(jobs, many=True)

        return Response({
            "alert_id": alert.id,
            "matched_jobs_count": jobs.count(),
            "matched_jobs": serializer.data
        })
    
class JobAlertNewCountAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LandingJobSerializer
    def get(self, request, alert_id):
        alert = get_object_or_404(
            JobAlert,
            id=alert_id,
            user=request.user,
            is_active=True
        )
        jobs = match_jobs(alert)

        if alert.last_read_at:
            jobs = jobs.filter(posted_on__gt=alert.last_read_at)

        serializer = self.get_serializer(jobs, many=True)

        return Response({
            "alert_id": alert.id,
            "new_matching_jobs_count": jobs.count(),
            "matched_jobs": serializer.data

        })




class JobCategoryListAPIView(ListAPIView):
    serializer_class = JobCategoryListSerializer
    
    def get_queryset(self):
        return JobCategory.objects.annotate(jobs_count=Count("jobs_category")).filter(is_active=True)




class JobCategoryAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LandingJobPagination

    def get(self, request, category_id):
        jobcategory = get_object_or_404(JobCategory, id=category_id)

        queryset = (
            Job.objects
            .filter(category=jobcategory)
            .order_by("-posted_on")
        )
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = JobcatSerializer(page, many=True)

        return paginator.get_paginated_response({
            "category_id": jobcategory.id,
            "category_name": jobcategory.name,
            "total_jobs": paginator.page.paginator.count,
            "jobs": serializer.data,
        })

# get jobseeker resume and get detail in resume and autofill

class ResumeUploadAPIView(GenericAPIView):
    serializer_class = ResumeUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):

        jobseeker, _ = JobSeeker.objects.get_or_create(user=request.user)
        resume= request.FILES.get("resume")
        serializer = self.get_serializer(
            jobseeker,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        parsed_data = {}
        profile_updated = False

        if jobseeker.resume:
            parsed_data = parse_resume_with_rapidapi(jobseeker.resume.path)
            data = parsed_data.get("data", {})

            if data:
                # 🔹 Name
                name = data.get("name")
                if name and not jobseeker.first_name:
                    parts = name.split()
                    jobseeker.first_name = parts[0]
                    jobseeker.last_name = parts[-1] if len(parts) > 1 else ""
                    profile_updated = True

                # 🔹 Education
                education_list = data.get("education", [])
                if education_list and not jobseeker.education:
                    degrees = [
                        edu.get("degree")
                        for edu in education_list
                        if edu.get("degree")
                    ]
                    jobseeker.education = ", ".join(degrees)
                    profile_updated = True

                # 🔹 Job Title
                experience_list = data.get("experience", [])
                if experience_list and not jobseeker.title:
                    jobseeker.title = experience_list[0].get("title", "")
                    profile_updated = True

                # 🔹 Skills (ManyToMany)
                skills_list = data.get("skills", [])
                if skills_list:
                    for skill_name in skills_list:
                        skill_obj, _ = Skill.objects.get_or_create(
                            name=skill_name.strip()
                        )
                        jobseeker.skills.add(skill_obj)

                    profile_updated = True

                if profile_updated:
                    jobseeker.save()
        create_activity_log(
                request.user,
                "UPLOADED_RESUME",
                "Uploaded or updated resume"
            )
        createversionccontrolresume(request.user,
        resume)
        return Response(
            {
                "detail": "Resume uploaded successfully",
                "resume": jobseeker.resume.url if jobseeker.resume else None,
                "profile_updated": profile_updated,
                "parsed_data": parsed_data
            },
            status=status.HTTP_200_OK
        )
    

#for completion percentage of profile

class ProfileCompletionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = calculate_profile_completion(request.user)
        return Response(data)
    


# for skill assessment score


class SkillAssessmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobseeker, _ = JobSeeker.objects.get_or_create(user=request.user)

        # Skill score (60%)
        skill_count = jobseeker.skills.count()
        skill_score = min(skill_count, 10) * 6   # max 60
        total_percentage_of_skill = round(((skill_score/60)*100),2)
        
        # Experience score (40%)
        total_years = calculate_total_experience(jobseeker)
        experience_score = min(total_years, 10) * 4   # max 40
        total_percentage_of_experience = round(((experience_score/40)*100),2)

        final_score = round(skill_score + experience_score)
        total_percentage_of_final = round(((final_score/100)*100),2)

        # Level classification
        if final_score <= 30:
            level = "Beginner"
        elif final_score <= 60:
            level = "Intermediate"
        elif final_score <= 85:
            level = "Advanced"
        else:
            level = "Expert"

        return Response({
            "total_skills": skill_count,
            "total_experience_years": total_years,
            "skill_score_&_Percentage": f"The Skill score is {skill_score} out of 60 and The Percenatage is {total_percentage_of_skill}%",
            "experience_score_&_Percentage":  f"The Experience score is {experience_score}  out of 40 and The Percenatage is {total_percentage_of_experience}%",
            "final_score":  f"The final core is {final_score} out of 100 and The Percenatage is {total_percentage_of_final}%",
            "level": level
        })
    

class AIChatbotAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatbotMessageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["message"]

        # 1️⃣ First check DB
        db_answer = find_best_answer(question)

        if db_answer:
            return Response({
                "source": "database",
                "reply": db_answer
            })

        # 2️⃣ Ask AI
        ai_reply = ask_ai(question)

        if not ai_reply or "CONTACT_SUPPORT" in ai_reply:
            # 3️⃣ Save to admin review
            UnansweredQuestion.objects.create(
                user=request.user,
                question=question
            )

            return Response({
                "source": "fallback",
                "reply": "Sorry, I couldn't answer this. Please contact support."
            })

        return Response({
            "source": "ai",
            "reply": ai_reply
        })
    


class JobseekerInterviewListAPIView(ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        return jobseeker.interviews.all().order_by("interview_date")
    

class JobseekerApplicationStatusAPIView(ListAPIView):
    serializer_class = JobseekerApplicationStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAppliedJob.objects.filter(user=self.request.user)




class JobViewTrackAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):

        job = get_object_or_404(Job, id=job_id)

        # Create only if not already viewed
        JobView.objects.get_or_create(
            job=job,
            user=request.user
        )
        create_activity_log(
            request.user,
            "VIEWED_JOB",
            f"Viewed {job.role} at {job.company.name}"
        )

        return Response({
            "message": "View recorded",
            "job_id": job.id
        })
    
class JobseekerPreferenceView(RetrieveUpdateAPIView):
    serializer_class = JobseekerPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        preference, created = JobseekerPreference.objects.get_or_create(
            user=self.request.user
        )
        create_activity_log(
    self.request.user,
    "UPDATED_PREFERENCE",
    "Updated job preferences"
)
        return preference
    

class RecommendedJobsAPIView(ListAPIView):
    serializer_class = LandingJobSerializer
    permission_classes = [IsAuthenticated]
    queryset = Job.objects.none()

    def list(self, request, *args, **kwargs):
        user = request.user
        cache_key = f"recommended_jobs_user_{user.id}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        jobs = generate_recommendations(user)

        serializer = self.get_serializer(jobs, many=True)
        response_data = serializer.data

        cache.set(cache_key, response_data, timeout=600)

        return Response(response_data)

class JobseekerPrivacySettingsAPIView(RetrieveUpdateAPIView):
    serializer_class = JobseekerPrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        settings_obj, created = JobseekerPrivacySettings.objects.get_or_create(
            user=self.request.user
        )
        create_activity_log(
    self.request.user,
    "UPDATED_PRIVACY",
    "Updated privacy settings"
)
        return settings_obj
    


class JobseekerActivityLogAPIView(ListAPIView):
    serializer_class = JobseekerActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobseekerActivityLog.objects.filter(
            user=self.request.user
        )
    

class JobRecommendationFeedbackAPIView(CreateAPIView):
    serializer_class = JobRecommendationFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        job = serializer.validated_data["job"]

        feedback, created = JobRecommendationFeedback.objects.update_or_create(
            user=user,
            job=job,
            defaults={
                "feedback_type": serializer.validated_data.get("feedback_type"),
                "rating": serializer.validated_data.get("rating"),
                "comment": serializer.validated_data.get("comment"),
            }
        )

        serializer.instance = feedback


class JobseekerDashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        cache_key = f"dashboard_summary_user_{user.id}"

        # 🔹 1️⃣ Cache check
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # 🔹 2️⃣ Aggregate counts (optimized queries)
        applied_qs = UserAppliedJob.objects.filter(user=user)
        saved_qs = UserSavedJob.objects.filter(user=user)
        alerts_qs = JobAlert.objects.filter(user=user)
        interviews = Interview.objects.filter(jobseeker__user=user)
        total_applied = applied_qs.count()
        total_saved = saved_qs.count()
        total_alerts = alerts_qs.count()
        total_interviews =interviews.count()

        
        # 🔹 3️⃣ Recent Applied Jobs (Optimized)
        recent_applied = list(
            applied_qs.select_related("job", "job__company")
            .order_by("-applied_at")[:5]
            .values(
                "job__id",
                "job__role",
                "job__company__name",
                "status",
                "applied_at"
            )
        )

        # 🔹 4️⃣ Recent Saved Jobs
        recent_saved = list(
            saved_qs.select_related("job", "job__company")
            .order_by("-saved_at")[:5]
            .values(
                "job__id",
                "job__role",
                "job__company__name",
                "saved_at"
            )
        )

        # 🔹 5️⃣ Top 3 Recommended Jobs
        recommended_jobs = generate_recommendations(user)[:3]

        recommended_data = [
            {
                "id": job.id,
                "role": job.role,
                "company": job.company.name,
                "score": getattr(job, "total_score", 0),
            }
            for job in recommended_jobs
        ]

        # Profile Completion Breakdown
        profile_data = calculate_profile_completion(user)

        # Engagement Metrics (Advanced Addition)
        engagement_score = calculate_engagement_score(
            total_applied,
            total_saved,
            total_alerts
        )

        #  Final Response Structure
        data = {
            "counts": {
                "total_applied_jobs": total_applied,
                "total_saved_jobs": total_saved,
                "total_interviews": total_interviews,
                "total_job_alerts": total_alerts,
            },
            "recent_activity": {
                "recent_applied_jobs": recent_applied,
                "recent_saved_jobs": recent_saved,
            },
            "recommended_jobs": recommended_data,
            "profile_completion": profile_data,
            "engagement_score": engagement_score
        }

        #   Cache result (5 minutes)
        cache.set(cache_key, data, timeout=300)

        return Response(data)


class AdvancedProfileStrengthAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = AdvancedProfileStrengthService(request.user)
        data = service.calculate()
        return Response(data)




class WeeklyJobMatchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = AdvancedWeeklyJobMatchService(request.user)
        return Response(service.calculate())
    



class ApplicationAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        applications = UserAppliedJob.objects.filter(user=user)

        total_applied = applications.count()
        selected_jobs = applications.filter(status="SELECTED").count()
        rejected_jobs = applications.filter(status="REJECTED").count()
        under_review = applications.filter(status="UNDER_REVIEW").count()


        success_rate = 0
        if total_applied > 0:
            success_rate = round((selected_jobs / total_applied) * 100, 2)

        response_times = []
        for app in applications.exclude(status="APPLIED"):
            response_times.append(
                (now() - app.applied_at).days
            )

        avg_response_time = 0
        if response_times:
            avg_response_time = round(sum(response_times) / len(response_times), 2)


        best_role = (
            applications
            .filter(status="SELECTED")
            .values("job__role")
            .annotate(count=Count("id"))
            .order_by("-count")
            .first()
        )

        best_company = (
            applications
            .filter(status="SELECTED")
            .values("job__company__name")
            .annotate(count=Count("id"))
            .order_by("-count")
            .first() 
        )

        return Response({
            "application_summary": {
                "total_applied": total_applied,
                "selected": selected_jobs,
                "rejected": rejected_jobs,
                "under_review": under_review
            },
            "success_rate": f"{success_rate}%",
            "average_response_time_days": avg_response_time,
            "best_performing_role": best_role["job__role"] if best_role else None,
            "best_company_response": best_company["job__company__name"] if best_company else None
        })


class JobseekerPerformanceInsightsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cache_key = f"jobseeker_performance_insights_{user.id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        applied_qs = UserAppliedJob.objects.filter(user=user).select_related(
            "job",
            "job__company",
        )
        saved_qs = UserSavedJob.objects.filter(user=user)
        viewed_qs = JobView.objects.filter(user=user)
        activity_qs = JobseekerActivityLog.objects.filter(user=user)

        total_applied = applied_qs.count()
        total_saved = saved_qs.count()
        total_viewed = viewed_qs.count()

        selected_count = applied_qs.filter(status="SELECTED").count()
        rejected_count = applied_qs.filter(status="REJECTED").count()
        under_review_count = applied_qs.filter(status="UNDER_REVIEW").count()
        pending_count = applied_qs.filter(status="APPLIED").count()
        processed_count = applied_qs.exclude(status="APPLIED").count()

        conversion_rate = round((selected_count / total_applied) * 100, 2) if total_applied else 0
        response_rate = round((processed_count / total_applied) * 100, 2) if total_applied else 0
        view_to_apply_rate = round((total_applied / total_viewed) * 100, 2) if total_viewed else 0
        save_to_apply_ratio = round((total_saved / total_applied), 2) if total_applied else 0

        since_30_days = now() - timedelta(days=30)

        last_30_days = {
            "applications": applied_qs.filter(applied_at__gte=since_30_days).count(),
            "saved_jobs": saved_qs.filter(saved_at__gte=since_30_days).count(),
            "job_views": viewed_qs.filter(viewed_at__gte=since_30_days).count(),
            "activities": activity_qs.filter(created_at__gte=since_30_days).count(),
        }

        total_alerts = JobAlert.objects.filter(user=user, is_active=True).count()
        profile_completion = calculate_profile_completion(user)
        engagement_score = calculate_engagement_score(
            total_applied,
            total_saved,
            total_alerts,
        )

        status_breakdown = list(
            applied_qs.values("status")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        top_applied_companies = list(
            applied_qs.values("job__company__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        recent_activity = list(
            activity_qs.values("action_type", "description", "created_at")[:10]
        )

        data = {
            "summary": {
                "total_applied_jobs": total_applied,
                "total_saved_jobs": total_saved,
                "total_viewed_jobs": total_viewed,
                "selected_jobs": selected_count,
                "rejected_jobs": rejected_count,
                "under_review_jobs": under_review_count,
                "pending_jobs": pending_count,
            },
            "performance": {
                "selection_conversion_rate_percent": conversion_rate,
                "employer_response_rate_percent": response_rate,
                "view_to_apply_rate_percent": view_to_apply_rate,
                "save_to_apply_ratio": save_to_apply_ratio,
                "engagement_score": engagement_score,
            },
            "profile": profile_completion,
            "application_status_breakdown": status_breakdown,
            "top_applied_companies": top_applied_companies,
            "last_30_days": last_30_days,
            "recent_activity": recent_activity,
            "generated_at": now(),
        }

        cache.set(cache_key, data, timeout=180)

        return Response(data)
    

class NearbyJobsAPIView(APIView):

    permission_classes = [AllowAny]
    pagination_class = LandingJobPagination

    def get(self, request):

        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")
        radius_km = float(request.GET.get("radius_km", 25))
        role = request.GET.get("role")

        if not latitude or not longitude:
            raise ValidationError(
                {"error": "latitude and longitude are required"}
            )

        latitude = float(latitude)
        longitude = float(longitude)

        jobs = NearbyJobService.get_nearby_jobs(
            latitude,
            longitude,
            radius_km,
            role,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(jobs, request)

        serializer = NearbyJobSerializer(page, many=True)

        return paginator.get_paginated_response(
            {
                "search_center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius_km": radius_km,
                "total_jobs": paginator.page.paginator.count,
                "jobs": serializer.data,
            }
        )
    


class NearbyJobsFromProfileAPIView(APIView):

    permission_classes = [IsAuthenticated]
    pagination_class = LandingJobPagination

    def get(self, request):

        try:
            jobseeker = JobSeeker.objects.get(user=request.user)
        except JobSeeker.DoesNotExist:
            return Response(
                {"error": "Jobseeker profile not found"},
                status=404
            )

        if not jobseeker.latitude or not jobseeker.longitude:
            return Response(
                {"message": "Please update your live location"},
                status=400
            )

        latitude = float(jobseeker.latitude)
        longitude = float(jobseeker.longitude)

        radius_km = float(request.GET.get("radius_km", 25))
        role = request.GET.get("role")

        jobs = NearbyJobService.get_nearby_jobs(
            latitude,
            longitude,
            radius_km,
            role,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(jobs, request)

        serializer = NearbyJobSerializer(page, many=True)

        return paginator.get_paginated_response(
            {
                "search_center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius_km": radius_km,
                "total_jobs": paginator.page.paginator.count,
                "jobs": serializer.data,
            }
        )
    
class SimilarJobsAPIView(APIView):

    permission_classes = [AllowAny]
    pagination_class = LandingJobPagination
    def get(self, request, job_id):

        try:
            job = Job.objects.select_related(
                "company",
                "category"
            ).prefetch_related(
                "skills_required"
            ).get(id=job_id)

        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)

        job_skills = job.skills_required.all()

        similar_jobs = (
            Job.objects.select_related("company", "category")
            .prefetch_related("skills_required")
            .filter(category=job.category)
            .exclude(id=job.id)
            .filter(
                Q(role__icontains=job.role) |
                Q(skills_required__in=job_skills)
            )
            .distinct()[:10]
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(similar_jobs, request)

        serializer = LandingJobSerializer(page, many=True)
        return paginator.get_paginated_response(
            {
                "total_jobs": paginator.page.paginator.count,
                "jobs": serializer.data,
            }
        )
    
class ProjectPortfolioListApiView(ListCreateAPIView):
    permission_classes =[IsAuthenticated]
    serializer_class = ProjectPortfolioSerializer
    def get_queryset(self):
        return ProjectPortfolio.objects.select_related("jobseeker__user").filter(jobseeker__user=self.request.user)
    def perform_create(self, serializer):
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        serializer.save(jobseeker=jobseeker)
    


class ProjectPortfolioListApiViewSpecific(RetrieveUpdateDestroyAPIView):
    permission_classes =[IsAuthenticated]
    serializer_class = ProjectPortfolioSerializer
    def get_queryset(self):
        pk= self.kwargs["pk"]
        return ProjectPortfolio.objects.select_related("jobseeker__user").filter(id=pk,jobseeker__user=self.request.user)


class ResumeToggleApiView(RetrieveUpdateAPIView):
    permission_classes =[IsAuthenticated]
    serializer_class = resumetoggleserializer
    def get_object(self):
        resume_option, created = resumetoggle.objects.select_related("user").get_or_create(
            user=self.request.user
        )
    
        return resume_option


class ResumeversionlistApi(ListAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class= resumeversioncontrolserializer
    def get_queryset(self):
        return versioncontrol.objects.select_related("user").filter(user=self.request.user).order_by("-updated_at")
    

class JobSeekerDocumentReceivedApi(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobseekerCertificateSerializer
    def perform_create(self, serializer):
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        serializer.save(jobseeker=jobseeker) 

    

class JobSeekerDocumentReceivedRUDApiView(RetrieveUpdateDestroyAPIView):
    permission_classes =[IsAuthenticated]
    serializer_class = JobseekerCertificateSerializer
    def get_queryset(self):
        pk= self.kwargs["pk"]
        return Jobseekercertificates.objects.select_related("jobseeker__user").filter(id=pk,jobseeker__user=self.request.user)
  


class JobSeekerEducationDetailsApi(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobseekerEducationDetailsSerializer
    def perform_create(self, serializer):
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        serializer.save(jobseeker=jobseeker)


class JobSeekerEducationDetailsRUDApiView(RetrieveUpdateDestroyAPIView):
    permission_classes =[IsAuthenticated]
    serializer_class = JobseekerEducationDetailsSerializer
    def get_queryset(self):
        pk= self.kwargs["pk"]
        qs = Jobseekereducationdetails.objects.select_related("jobseeker__user").filter(id=pk,jobseeker__user=self.request.user)
        return qs

class JobSeekerExperienceDetailsApi(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobseekerExperienceSerializers
    def perform_create(self, serializer):
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        serializer.save(jobseeker=jobseeker)    
       
class JobSeekerExperienceRUDApiView(RetrieveUpdateDestroyAPIView):
    permission_classes =[IsAuthenticated]
    serializer_class = JobseekerExperienceSerializers
    lookup_field= "uuid"
    lookup_url_kwarg="uuid"
    def get_queryset(self):
        qs = JobExperience.objects.select_related("jobseeker__user").filter(jobseeker__user=self.request.user)
        return qs
    




class JobSeekerSkillsAPI(GenericAPIView):
    serializer_class = JobseekerSkillsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Jobseekerskills.objects.select_related(
            "jobseeker__user"
        ).prefetch_related("skills")

    def get_object(self):

        jobseeker, _ = JobSeeker.objects.get_or_create(
            user=self.request.user
        )

        obj, _ = self.get_queryset().get_or_create(
            jobseeker=jobseeker
        )

        return obj, jobseeker

    
    def get(self, request):
        skills_obj, _ = self.get_object()

        serializer = self.get_serializer(skills_obj)
        return Response(serializer.data)

  
    def post(self, request):
        skills_obj, jobseeker = self.get_object()

        serializer = self.get_serializer(
            skills_obj,   
            data=request.data,
            partial=True,
            context={"jobseeker": jobseeker}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

  
    def patch(self, request):
        skills_obj, jobseeker = self.get_object()

        serializer = self.get_serializer(
            skills_obj,
            data=request.data,
            partial=True,
            context={"jobseeker": jobseeker}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request):
        skills_obj, _ = self.get_object()

        skills_obj.skills.clear()
        skills_obj.custom_skills = ""   
        skills_obj.save()

        return Response(
            {"message": "Skills removed successfully"},
            status=204
        )