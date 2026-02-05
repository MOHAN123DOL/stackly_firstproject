from django.urls import path
from .views import (
    OpenChatAPIView,
    SendMessageAPIView,
    MessageListAPIView,
    MarkMessagesReadAPIView
)

urlpatterns = [
    path("open/", OpenChatAPIView.as_view()),
    path("send/", SendMessageAPIView.as_view()),
    path(
        "conversation/<int:conversation_id>/messages/",
        MessageListAPIView.as_view()
    ),
    path("read/", MarkMessagesReadAPIView.as_view()),
]
