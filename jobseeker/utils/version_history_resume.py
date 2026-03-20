from jobseeker.models import versioncontrol

def createversionccontrolresume(user,data):
    version=versioncontrol.objects.filter(user=user).order_by("-updated_at").first()
    if version is None:
        version_age = 1
    else:
        version_age=1+version.version
    versioncontrol.objects.create(
        user=user,
        resumes=data,
        version= version_age
    )

