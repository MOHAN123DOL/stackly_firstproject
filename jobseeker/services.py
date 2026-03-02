from .models import JobSeeker , Job, UserAppliedJob , UserSavedJob , Company
from django.core.cache import cache

from celery import shared_task
from django.core.cache import cache
from .models import JobSeeker
from .utils.total_experiences_calculator import calculate_total_experience
from .models import HelpIntent , JobseekerActivityLog
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from datetime import date

from .models import (
    JobSeeker,
    Job,
    Skill,
    UserAppliedJob,
    UserSavedJob,
    JobView,
)
import requests
from django.conf import settings


cache_timeout = 300
def get_opportunities_overview(user):
    cache_key = f"jobseeker_overview_{user.id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data

    jobseeker = JobSeeker.objects.get(user=user)

    # Default values
    recommended_jobs = []
    recommended_message = None

    # 🔥 Recommended jobs logic
    if not jobseeker.title:
        recommended_message = "Please add your role in your profile"
    else:
        recommended_message = f'For your Job Title {jobseeker.title} '
        qs = Job.objects.filter(
        role__icontains=jobseeker.title
        ).select_related("company").order_by("-posted_on")[:5]

        recommended_jobs = list(
            qs.values(
                "id",
                "role",
                "company__name",
                "posted_on"
            )
        )
    

    data = {
        "total_jobs": Job.objects.count(),
        "total_companies": Company.objects.count(),
        "applied_jobs": UserAppliedJob.objects.filter(user=user).count(),
        "saved_jobs": UserSavedJob.objects.filter(user=user).count(),

        "recommended_message": recommended_message,
        "recommended_count": len(recommended_jobs),
        "recommended_jobs": recommended_jobs,
    }

    cache.set(cache_key, data, cache_timeout)
    return data



def find_best_answer(user_message):
    user_message = user_message.lower()

    intents = HelpIntent.objects.all()

    best_match = None
    highest_score = 0

    for intent in intents:
        score = 0
        keywords = intent.keywords.lower().split(",")

        for word in keywords:
            if word.strip() in user_message:
                score += 1

        if score > highest_score:
            highest_score = score
            best_match = intent

    if best_match:
        return best_match.answer

    return None





def ask_ai(question):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful job portal support assistant. If you don't know the answer, reply with CONTACT_SUPPORT."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data["choices"][0]["message"]["content"]

    print("Groq Error:", response.text)
    return None




def create_activity_log(user, action_type, description=""):
    JobseekerActivityLog.objects.create(
        user=user,
        action_type=action_type,
        description=description
    )





class AdvancedProfileStrengthService:

    MAX_SCORE = 120

    def __init__(self, user):
        self.user = user
        self.score = 0
        self.breakdown = {}
        self.suggestions = []

        try:
            self.jobseeker = JobSeeker.objects.get(user=user)
        except ObjectDoesNotExist:
            self.jobseeker = None

    
    def calculate(self):

        if not self.jobseeker:
            return {
                "total_score": 0,
                "percentage": 0,
                "level": "Incomplete",
                "breakdown": {},
                "priority_improvements": [
                    {"action": "Complete profile setup", "impact_score": 50}
                ],
            }

        self._core_profile()
        self._professional_strength()
        self._role_based_skill_analysis()
        self._engagement()
        self._optimization()
        self._bonus()

        percentage = min(int((self.score / self.MAX_SCORE) * 100), 100)

        return {
            "total_score": f"{self.score} out of {self.MAX_SCORE}",
            "percentage": f"{percentage}%",
            "level": self._get_level(percentage),
            "breakdown": self.breakdown,
            "priority_improvements": self._priority_sort(),
        }

    def _add_suggestion(self, message, impact):
        if message not in [s[0] for s in self.suggestions]:
            self.suggestions.append((message, impact))

  
    def _core_profile(self):
        core_score = 0

        if self.jobseeker.first_name and self.jobseeker.last_name:
            core_score += 10
        else:
            self._add_suggestion("Add full name", 10)

        if self.jobseeker.title:
            core_score += 5
        else:
            self._add_suggestion("Add professional title", 5)

        if self.jobseeker.education:
            core_score += 10
        else:
            self._add_suggestion("Add education details", 10)

        if self.jobseeker.resume:
            core_score += 15
        else:
            self._add_suggestion("Upload resume", 15)

        if self.jobseeker.avatar:
            core_score += 10
        else:
            self._add_suggestion("Upload profile photo", 10)

        self.score += core_score
        self.breakdown["core_profile"] = core_score

    def _role_based_skill_analysis(self):

        if not self.jobseeker.title:
            self._add_suggestion(
                "Add professional title to enable skill matching", 10
            )
            self.breakdown["skill_alignment"] = 0
            return

        related_jobs = Job.objects.filter(
            role__icontains=self.jobseeker.title
        ).prefetch_related("skills_required")

        if not related_jobs:
            self.breakdown["skill_alignment"] = 0
            return

        required_skills = set()

        for job in related_jobs:
            for skill in job.skills_required.all():
                required_skills.add(skill.id)

        if not required_skills:
            self.breakdown["skill_alignment"] = 0
            return

        user_skills = set(
            self.jobseeker.skills.values_list("id", flat=True)
        )

        matched = user_skills.intersection(required_skills)

        match_percentage = int(
            (len(matched) / len(required_skills)) * 100
        )

        if match_percentage >= 70:
            score = 15
        elif match_percentage >= 40:
            score = 8
            self._add_suggestion(
                "Improve skill alignment with target role", 7
            )
        else:
            score = 3
            self._add_suggestion(
                "Add role-relevant skills", 15
            )

        missing_skill_ids = required_skills - user_skills

        missing_skills = Skill.objects.filter(
            id__in=missing_skill_ids
        ).values_list("name", flat=True)

        self.breakdown["skill_alignment"] = score
        self.breakdown["skill_match_percentage"] = match_percentage
        self.breakdown["missing_recommended_skills"] = list(missing_skills)[:5]

        self.score += score

  
    def _professional_strength(self):
        prof_score = 0

        total_experience_years = self._calculate_experience()

        if total_experience_years >= 5:
            prof_score += 10
        elif total_experience_years > 0:
            prof_score += 5
            self._add_suggestion("Add more experience details", 5)
        else:
            self._add_suggestion("Add work experience", 10)

        if self.jobseeker.title:
            prof_score += 5

        self.score += prof_score
        self.breakdown["professional_strength"] = prof_score


    def _engagement(self):
        engagement_score = 0

        applied = UserAppliedJob.objects.filter(user=self.user).count()
        saved = UserSavedJob.objects.filter(user=self.user).count()
        views = JobView.objects.filter(user=self.user).count()

        if applied >= 3:
            engagement_score += 5
        if saved >= 2:
            engagement_score += 3
        if views >= 5:
            engagement_score += 2

        self.score += engagement_score
        self.breakdown["engagement"] = engagement_score

    def _optimization(self):
        opt_score = 0

        if hasattr(self.user, "preferences"):
            opt_score += 5
        else:
            self._add_suggestion("Set job preferences", 5)

        if hasattr(self.user, "privacy_settings"):
            opt_score += 5

        self.score += opt_score
        self.breakdown["optimization"] = opt_score

    def _bonus(self):
        bonus = 0

        if self.jobseeker.resume:
            if self.jobseeker.resume.name.endswith(".pdf"):
                bonus += 10
            else:
                self._add_suggestion(
                    "Upload resume in PDF format (ATS friendly)", 5
                )

        if hasattr(self.user, "preferences"):
            pref_skills = self.user.preferences.preferred_skills.count()
            if pref_skills:
                bonus += 10

        self.score += bonus
        self.breakdown["bonus"] = bonus

    def _calculate_experience(self):
        total = 0

        for exp in self.jobseeker.experiences.all():
            if exp.end_date:
                total += (exp.end_date - exp.start_date).days / 365
            else:
                total += (date.today() - exp.start_date).days / 365

        return int(total)

    def _priority_sort(self):
        return [
            {"action": s[0], "impact_score": s[1]}
            for s in sorted(self.suggestions, key=lambda x: x[1], reverse=True)
        ]


    def _get_level(self, percentage):
        if percentage >= 85:
            return "Elite"
        elif percentage >= 70:
            return "Strong"
        elif percentage >= 50:
            return "Moderate"
        else:
            return "Needs Improvement"