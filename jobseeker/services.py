from .models import JobSeeker , Job, UserAppliedJob , UserSavedJob , Company
from django.core.cache import cache

from celery import shared_task
from django.core.cache import cache
from .models import JobSeeker
from .utils.total_experiences_calculator import calculate_total_experience
from .models import HelpIntent

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