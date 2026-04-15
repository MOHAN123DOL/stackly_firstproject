from celery import shared_task
from employees.models import Interview
from notifications.utils import create_notification
from django.utils import timezone

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