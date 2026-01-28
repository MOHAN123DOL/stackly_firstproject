from django.db import migrations


def clear_job_tables(apps, schema_editor):
    UserAppliedJob = apps.get_model("jobseeker", "UserAppliedJob")
    UserSavedJob = apps.get_model("jobseeker", "UserSavedJob")

    UserAppliedJob.objects.all().delete()
    UserSavedJob.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
       ("jobseeker", "0007_delete_job"),

    ]

    operations = [
        migrations.RunPython(clear_job_tables),
    ]
