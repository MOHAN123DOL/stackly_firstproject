from rest_framework import serializers
from .models import LandingChoice
from .models import InfoCard
from .services import get_infocard_count
class LandingChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingChoice
        fields = [
            "id",
            "role",
            "title",
            "description",
            "redirect_url",
        ]



class InfoCardSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()

    class Meta:
        model = InfoCard
        fields = ["key", "title", "icon", "count"]

    def get_count(self, obj):
        return get_infocard_count(obj.key)
