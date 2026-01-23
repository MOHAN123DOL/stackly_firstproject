from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)   # ✅ NEW
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

