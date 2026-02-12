
from datetime import date
def calculate_total_experience(jobseeker):
    total_days = 0

    for exp in jobseeker.experiences.all():
        start = exp.start_date
        end = date.today() if exp.is_current or not exp.end_date else exp.end_date
        total_days += (end - start).days

    return round(total_days / 365, 1)