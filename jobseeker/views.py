from rest_framework.generics import GenericAPIView , ListAPIView , CreateAPIView , RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.images import get_image_dimensions
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import BasePermission
from .models import JobSeeker , UserAppliedJob, UserSavedJob ,Company, Job , JobAlert , JobCategory , Skill , JobView
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
   
    
)


from employees.serializers import InterviewSerializer
from .models import UnansweredQuestion
from .services import ask_ai , find_best_answer
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from notifications.utils import create_notification
from notifications.models import Notification
from django.utils.timezone import now
from datetime import timedelta
from rest_framework.views import APIView
from django.db.models import Count
from django.contrib.auth.models import User
from employees.models import Employee
from .services import get_opportunities_overview
from .pagination import LandingJobPagination
from django.db.models.functions import Lower
from .utils.Matching import match_jobs
from .serializers import ResumeUploadSerializer
from.utils.resume_apyhub import parse_resume_with_rapidapi 
from datetime import date
from.utils.total_experiences_calculator import calculate_total_experience

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


class JobSeekerRegistrationAPI(CreateAPIView):

    serializer_class = JobSeekerRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        create_notification(user, "Registration completed successfully")

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

    def put(self, request):
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

        create_notification(
            request.user,
            "Profile updated successfully"
        )

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

    def get(self, request):
        qs = Job.objects.select_related("company").annotate(
    view_count=Count("views", distinct=True),
    application_count=Count("applications", distinct=True))

        # 🔹 Single-value filters
        role = request.GET.get("role")
        salary = request.GET.get("salary")
        company = request.GET.get("company")

        # 🔹 Multi-value filters
        locations = request.GET.get("location")
        durations = request.GET.get("duration")
        salary_min = request.GET.get("salary_min")
        salary_max = request.GET.get("salary_max")

        if salary_min:
            qs = qs.filter(salary_max__gte=int(salary_min))

        if salary_max:
            qs = qs.filter(salary_min__lte=int(salary_max))

        if role:
            qs = qs.filter(role__icontains=role)

        if salary:
            qs = qs.filter(salary__icontains=salary)

        if company:
            company_list = [c.strip() for c in company.split(",")]
            qs = qs.filter(company__name__in=company_list)

        if locations:
            location_list = [l.strip().lower() for l in locations.split(",")]
            qs = qs.annotate(
                location_lower=Lower("company__location")
            ).filter(location_lower__in=location_list)

        if durations:
            duration_list = [d.strip().lower() for d in durations.split(",")]
            qs = qs.annotate(
                duration_lower=Lower("duration")
            ).filter(duration_lower__in=duration_list)

        # 🔹 Sort latest first
        qs = qs.order_by("-posted_on")

        # 🔹 Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)

        serializer = LandingJobSerializer(page, many=True)

        return paginator.get_paginated_response({
            "total_jobs": qs.count(),
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
        jobseeker, _ = JobSeeker.objects.get_or_create(user=request.user)

        sections = {
            "first_name": bool(jobseeker.first_name),
            "last_name": bool(jobseeker.last_name),
            "education": bool(jobseeker.education),
            "title": bool(jobseeker.title),
            "avatar": bool(jobseeker.avatar),
            "resume": bool(jobseeker.resume),
            "skills": jobseeker.skills.exists(),
            "experience": jobseeker.experiences.exists(),
        }

        total = len(sections)
        filled = sum(sections.values())
        percentage = round((filled / total) * 100)

        missing = []   

        for field, status in sections.items():
            if status == False:    
                missing.append(field)

        return Response({
            "completion_percentage": f"{percentage}%" ,
            "total_fields": total,
            "filled_fields": filled,
            "missing_fields": missing
        })
    


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

        return Response({
            "message": "View recorded",
            "job_id": job.id
        })