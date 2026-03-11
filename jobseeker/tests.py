from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from jobseeker.models import (
    Company,
    Job,
    JobCategory,
    JobSeeker,
    JobseekerActivityLog,
    ProjectPortfolio,
    Skill,
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


class LandingJobAdvancedFilterAPITest(APITestCase):
    def setUp(self):
        self.url = reverse("jobseeker-landing-joblisting")
        self.category = JobCategory.objects.create(name="Frontend")

        self.remote_company = Company.objects.create(
            name="Remote Tech",
            location="Remote",
        )
        self.hybrid_company = Company.objects.create(
            name="Hybrid Labs",
            location="Hybrid - Bangalore",
        )
        self.onsite_company = Company.objects.create(
            name="Onsite Works",
            location="Chennai",
        )

        self.python = Skill.objects.create(name="Python")
        self.django = Skill.objects.create(name="Django")
        self.react = Skill.objects.create(name="React")

        self.remote_job = Job.objects.create(
            company=self.remote_company,
            category=self.category,
            role="Backend Engineer",
            duration="Full-time",
            min_experience=2,
            salary_min=8,
            salary_max=15,
        )
        self.remote_job.skills_required.set([self.python, self.django])

        self.hybrid_job = Job.objects.create(
            company=self.hybrid_company,
            category=self.category,
            role="Python Developer",
            duration="Full-time",
            min_experience=4,
            salary_min=12,
            salary_max=20,
        )
        self.hybrid_job.skills_required.set([self.python])

        self.onsite_job = Job.objects.create(
            company=self.onsite_company,
            category=self.category,
            role="React Developer",
            duration="Contract",
            min_experience=1,
            salary_min=4,
            salary_max=7,
        )
        self.onsite_job.skills_required.set([self.react])

    def test_filters_experience_salary_remote_and_skills(self):
        response = self.client.get(
            self.url,
            {
                "experience": 3,
                "salary_min": 7,
                "salary_max": 16,
                "remote": "true",
                "skills": "python",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jobs = response.data["results"]["jobs"]
        job_ids = [job["id"] for job in jobs]

        self.assertIn(self.remote_job.id, job_ids)
        self.assertNotIn(self.hybrid_job.id, job_ids)
        self.assertNotIn(self.onsite_job.id, job_ids)

    def test_skills_match_all_requires_all_skills(self):
        response = self.client.get(
            self.url,
            {
                "skills": "python,django",
                "skills_match": "all",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jobs = response.data["results"]["jobs"]
        job_ids = [job["id"] for job in jobs]

        self.assertIn(self.remote_job.id, job_ids)
        self.assertNotIn(self.hybrid_job.id, job_ids)
        self.assertNotIn(self.onsite_job.id, job_ids)

    def test_invalid_salary_filter_returns_bad_request(self):
        response = self.client.get(
            self.url,
            {"salary_min": "not-a-number"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("salary_min", response.data)


class NearbyJobsAPITest(APITestCase):
    def setUp(self):
        self.url = reverse("nearby-jobs")
        self.category = JobCategory.objects.create(name="Mobile")

        self.nearest_company = Company.objects.create(
            name="Nearest Tech",
            location="Bengaluru",
            latitude=12.97160,
            longitude=77.59460,
        )
        self.second_company = Company.objects.create(
            name="Second Tech",
            location="Bengaluru East",
            latitude=12.93520,
            longitude=77.62450,
        )
        self.far_company = Company.objects.create(
            name="Far Tech",
            location="Chennai",
            latitude=13.08270,
            longitude=80.27070,
        )

        self.nearest_job = Job.objects.create(
            company=self.nearest_company,
            category=self.category,
            role="Android Developer",
            duration="Full-time",
            salary_min=8,
            salary_max=15,
        )
        self.second_job = Job.objects.create(
            company=self.second_company,
            category=self.category,
            role="Flutter Developer",
            duration="Full-time",
            salary_min=7,
            salary_max=14,
        )
        self.far_job = Job.objects.create(
            company=self.far_company,
            category=self.category,
            role="iOS Developer",
            duration="Contract",
            salary_min=10,
            salary_max=18,
        )

    def test_returns_jobs_within_radius_sorted_by_distance(self):
        response = self.client.get(
            self.url,
            {
                "latitude": 12.97160,
                "longitude": 77.59460,
                "radius_km": 20,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jobs = response.data["results"]["jobs"]
        job_ids = [job["id"] for job in jobs]

        self.assertEqual(response.data["results"]["total_jobs"], 2)
        self.assertEqual(job_ids, [self.nearest_job.id, self.second_job.id])
        self.assertNotIn(self.far_job.id, job_ids)
        self.assertLessEqual(jobs[0]["distance_km"], jobs[1]["distance_km"])

    def test_missing_latitude_returns_bad_request(self):
        response = self.client.get(
            self.url,
            {
                "longitude": 77.59460,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("latitude", response.data)

    def test_invalid_radius_returns_bad_request(self):
        response = self.client.get(
            self.url,
            {
                "latitude": 12.97160,
                "longitude": 77.59460,
                "radius_km": 0,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("radius_km", response.data)


class ProjectPortfolioAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="portfolio_user",
            email="portfolio@example.com",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="StrongPass123!",
        )

        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("project-portfolio-list-create")

    def test_create_and_list_project_portfolio(self):
        create_response = self.client.post(
            self.list_url,
            {
                "title": "Job Portal Revamp",
                "description": "Rebuilt the job search flow with DRF APIs.",
                "tech_stack": "Django, DRF, PostgreSQL",
                "project_url": "https://example.com/portfolio/project",
                "github_url": "https://github.com/example/project",
                "start_date": "2025-01-01",
                "end_date": "2025-06-30",
                "is_ongoing": False,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectPortfolio.objects.filter(jobseeker__user=self.user).count(), 1)

        list_response = self.client.get(self.list_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["title"], "Job Portal Revamp")

    def test_user_cannot_access_another_users_project(self):
        other_jobseeker = JobSeeker.objects.create(user=self.other_user)
        other_project = ProjectPortfolio.objects.create(
            jobseeker=other_jobseeker,
            title="Other User Project",
            description="Private project",
        )
        detail_url = reverse("project-portfolio-detail", kwargs={"pk": other_project.id})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_date_range_returns_bad_request(self):
        response = self.client.post(
            self.list_url,
            {
                "title": "Invalid Dates Project",
                "start_date": "2025-10-01",
                "end_date": "2025-02-01",
                "is_ongoing": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", response.data)
