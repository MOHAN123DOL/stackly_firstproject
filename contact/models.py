from django.db import models



class ContactMessage(models.Model):

    name = models.CharField(max_length=150)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    message = models.TextField()

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.email}"

