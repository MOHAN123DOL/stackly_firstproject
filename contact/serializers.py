from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "contact", "message", "created_at"]
        read_only_fields = ["id", "created_at"]
        
    def validate(self, attrs):

        name = attrs.get("name").strip()
        email = attrs.get("email").lower().strip()
        contact = attrs.get("contact").strip()
        message = attrs.get("message").strip()

        attrs["email"] = email
        attrs["name"] = name
        attrs["contact"] = contact
        attrs["message"] = message

        if len(message) <= 5:
            raise serializers.ValidationError(
                {"MESSAGE": "message can be 5 or more characters."}
            )

        if not contact.isdigit():
            raise serializers.ValidationError(
                {"contact": "Contact must contain only digits."}
            )

        if len(contact) != 10:
            raise serializers.ValidationError(
                {"contact": "Contact must be 10 digits."}
            )

        ten_minutes_ago = timezone.now() - timedelta(minutes=10)

        if   ContactMessage.objects.filter(
            email=email,
            created_at__gte=ten_minutes_ago
        ).exists():
            raise serializers.ValidationError(
                {"email": "You can submit only once every 10 minutes."}
            )
      
        return attrs

