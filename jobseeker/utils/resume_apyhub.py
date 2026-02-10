import requests
from django.conf import settings

RAPIDAPI_URL = "https://resumeparser-api.p.rapidapi.com"


def parse_resume_with_rapidapi(file_path: str) -> dict:
    headers = {
        "x-rapidapi-key": settings.RAPIDAPI_KEY,
        "x-rapidapi-host": "resumeparser-api.p.rapidapi.com"
    }

    try:
        with open(file_path, "rb") as f:
            files = {"resume": f}   

            response = requests.post(
                RAPIDAPI_URL,
                headers=headers,
                files=files,
                timeout=60
            )

        print("RAPID STATUS:", response.status_code)
        print("RAPID RESPONSE:", response.text)

        if response.status_code != 200:
            return {}

        return response.json()

    except Exception as e:
        print("RAPID ERROR:", str(e))
        return {}
