from rest_framework.generics import CreateAPIView 
from rest_framework.permissions import AllowAny
from .models import ContactMessage
from .serializers import ContactMessageSerializer
from .permission import IsNotStaff
from .throttles import ContactAnonThrottle, ContactUserThrottle

class ContactMessageCreateAPIView(CreateAPIView):

    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny, IsNotStaff]

    throttle_classes = [
        ContactAnonThrottle,
        ContactUserThrottle,
    ]
