from django.shortcuts import render
from rest_framework.generics import GenericAPIView , ListAPIView
from .serializers import LandingChoiceSerializer
from django.contrib.auth.models import User
from employees.models import Employee
from jobseeker.models import Job 
from .models import LandingChoice
from rest_framework.response import Response
from .models import InfoCard
from .serializers import InfoCardSerializer

class LandingChoiceAPI(ListAPIView):
    permission_classes = []
    serializer_class = LandingChoiceSerializer

    def get_queryset(self):
        return LandingChoice.objects.filter(is_active=True).order_by("id")[:2]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        job_count = Job.objects.count()
        employee_count = Employee.objects.count()

        # JobSeekers = users who are NOT staff and NOT superuser
        jobseeker_count = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).count()

        data = []
        for choice in queryset:
            item = LandingChoiceSerializer(choice).data

            if choice.role == "jobseeker":
                item["count_text"] = f"{job_count}+ Jobs available  &&  {employee_count}+ Employer are ready to hire you"
            elif choice.role == "employer":
                item["count_text"] = f"{jobseeker_count}+ job seekers available"
            else:
                item["count_text"] = ""

            data.append(item)

        return Response(data)




class LandingInfoCardAPI(ListAPIView):
    serializer_class = InfoCardSerializer
    permission_classes = []
    authentication_classes = []

    def get_queryset(self):
        return InfoCard.objects.filter(is_active=True).order_by("order")

