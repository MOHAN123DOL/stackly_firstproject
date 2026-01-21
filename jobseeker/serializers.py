from rest_framework import serializers
from .models import JobSeeker     
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User

class JobSeekerAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSeeker
        fields = ['avatar']



class JobSeekerRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True,style={'input_type': 'password'})

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}
            )

        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "Username already exists"}
            )

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "Email already exists"}
            )

        return data

    def create(self, validated_data):
        user = User(
        username=validated_data['username'],
        email=validated_data.get('email')
    )
        user.set_password(validated_data['password']) 
        user.save()
        # create empty jobseeker profile
        JobSeeker.objects.create(user=user)
        return user



class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # custom response fields
        data["message"] = f"Welcome {self.user.username}"
        data["username"] = self.user.username
        data["profile_url"] = "/jobseeker/profile/"

        return data



class JobSeekerProfileSerializer(serializers.ModelSerializer):
    welcome = serializers.SerializerMethodField()

    class Meta:
        model = JobSeeker
        fields = [
            "welcome",
            "first_name",
            "last_name",
            "education",
            "experience",
            "avatar",
        ]

    def get_welcome(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return f"Welcome {request.user.username}"
        return "Welcome"


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True,style={'input_type': 'password'})

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("New passwords do not match")
        return data


