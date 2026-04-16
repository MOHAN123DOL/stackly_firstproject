from celery import shared_task
from employees.models import Interview
from notifications.utils import create_notification
from django.utils import timezone
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings

from jobseeker.models import JobAlert
from jobseeker.utils.Matching import match_jobs

@shared_task
def send_interview_reminder(interview_id):

    interview = Interview.objects.get(id=interview_id)

    user = interview.jobseeker.user

    print(f"🔥 Sending reminder for interview {interview.id}")

    create_notification(
        user,
        f"Reminder: Your interview for {interview.job.role} starts in 1 hour"
    )
    print("TASK STARTED")
    print("Current UTC Time:", timezone.now())
    print("Interview UTC Time:", interview.interview_date)

    interview.reminder_sent_1hr = True
    interview.save(update_fields=["reminder_sent_1hr"])
    





@shared_task
def send_job_alert_emails():
    alerts = JobAlert.objects.filter(is_active=True).select_related("user")
    print("TASK STARTED")

    alerts = JobAlert.objects.filter(is_active=True)

    print("Alerts count:", alerts.count())

    for alert in alerts:
        print("Processing alert:", alert.id)

        jobs = match_jobs(alert)

        print("Total jobs:", jobs.count())

        if alert.last_notified_at:
            jobs = jobs.filter(posted_on__gt=alert.last_notified_at)

        print("New jobs count:", jobs.count())
        try:
            # 🔹 Step 1: Get matching jobs
            jobs = match_jobs(alert).select_related("company")

            # 🔹 Step 2: Filter only NEW jobs
            if alert.last_notified_at:
                jobs = jobs.filter(posted_on__gt=alert.last_notified_at)

            # 🔹 Step 3: Check if new jobs exist
            if not jobs.exists():
                continue

            # 🔹 Step 4: Prepare job list (limit to 5)
            job_list = []
            for job in jobs[:5]:
                company_name = getattr(job.company, "name", "Unknown")
                job_list.append(f"- {job.role} at {company_name}")

            job_text = "\n".join(job_list)

            # 🔹 Step 5: Build email message
            message = f"""
You have new job alerts for {alert.role}:

{job_text}

Login to your account to apply now.
"""
            print("SENDING EMAIL TO: ",alert.user.email)

            # 🔹 Step 6: Send email
            send_mail(
                subject="New Job Alert",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alert.user.email],
                fail_silently=False,
            )

            # 🔹 Step 7: Update last_notified_at
            alert.last_notified_at = now()
            alert.save(update_fields=["last_notified_at"])

        except Exception as e:
            print(f"Error processing alert {alert.id}: {str(e)}")