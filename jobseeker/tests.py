from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from jobseeker.models import (
    Company,
    Job,
    JobCategory,
    JobseekerActivityLog,
    JobView,
    UserAppliedJob,
    UserSavedJob,
)


class JobseekerPerformanceInsightsAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="insights_user",
            email="insights@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(user=self.user)

        self.company = Company.objects.create(name="Acme Corp")
        self.category = JobCategory.objects.create(name="Backend")

        self.job = Job.objects.create(
            company=self.company,
            category=self.category,
            role="Backend Developer",
            duration="Full-time",
            salary_min=600000,
            salary_max=1200000,
        )

        UserAppliedJob.objects.create(
            user=self.user,
            job=self.job,
            status="UNDER_REVIEW",
        )
        UserSavedJob.objects.create(user=self.user, job=self.job)
        JobView.objects.create(user=self.user, job=self.job)
        JobseekerActivityLog.objects.create(
            user=self.user,
            action_type="VIEWED_JOB",
            description="Viewed Backend Developer role",
        )

    def test_performance_insights_returns_expected_keys(self):
        url = reverse("jobseeker-performance-insights")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)
        self.assertIn("performance", response.data)
        self.assertIn("profile", response.data)
        self.assertIn("application_status_breakdown", response.data)
        self.assertIn("top_applied_companies", response.data)
        self.assertIn("last_30_days", response.data)
        self.assertIn("recent_activity", response.data)
