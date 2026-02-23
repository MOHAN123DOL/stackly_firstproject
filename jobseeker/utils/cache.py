from django.core.cache import cache


def clear_user_recommendation_cache(user_id):
    """
    Clears recommendation cache for a specific user
    """
    cache_key = f"recommended_jobs_user_{user_id}"
    #cache.delete(cache_key)


def clear_all_recommendation_cache():
    """
    Clears all recommendation caches.
    Use carefully in production.
    """
    #cache.clear()