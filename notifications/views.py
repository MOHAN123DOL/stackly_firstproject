from rest_framework.generics import ListAPIView , GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Notification
from .serializers import NotificationSerializer

class NotificationListAPI(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


class NotificationDetailAPI(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_object(self, request, id):
        try:
            return Notification.objects.get(
                id=id,
                user=request.user
            )
        except Notification.DoesNotExist:
            return None

    # GET → show details
    def get(self, request, id):
        notification = self.get_object(request, id)
        if not notification:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE → delete notification
    def delete(self, request, id):
        notification = self.get_object(request, id)
        if not notification:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        notification.delete()
        return Response(
            {"message": "Notification deleted successfully"},
            status=status.HTTP_200_OK
        )
