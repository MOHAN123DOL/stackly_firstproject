from django.shortcuts import render
from jobseeker.models import JobSeeker,Job,Company,UserAppliedJob
from employees.models import Employee
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny,IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q



class AdminOverviewDashboard(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        total_jobseekers=JobSeeker.objects.all().count()
        total_employees = Employee.objects.all().count()
        total_jobs = Job.objects.all().count()
        total_compnay = Company.objects.all().count()
        jobs = UserAppliedJob.objects.select_related("job")
        
        datas = jobs.values("job__role","job__company__name").annotate(
                new_count=Count("id", filter=Q(status="APPLIED")),
                waiting_count=Count("id", filter=Q(status="UNDER_REVIEW") | Q(status="SHORTLISTED")),
                total_count=Count("id"))
        qss = UserAppliedJob.objects.aggregate(
            applicants=Count("id", filter=Q(status="APPLIED")),
            recommended=Count("id", filter=Q(status="SHORTLISTED")),
            rejected=Count("id", filter=Q(status="REJECTED")),
            hired=Count("id", filter=Q(status="SELECTED")),
        )
        

        return Response (
            {"overview":{"total_jobseeker":total_jobseekers,
                "total_employee":total_employees,
                "total_jobs":total_jobs,
                "total_company":total_compnay,
                "total_job_user_apply":datas.count()}
                ,

              "applied_details_jobwise":{
                "data":datas,
                "qss":qss
                }

            },status=status.HTTP_200_OK

        )
