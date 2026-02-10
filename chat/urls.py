from django.urls import path
from .views import (
    OpenChatAPIView,
    SendMessageAPIView,
    MessageListAPIView,

    InboxAPIView
)

urlpatterns = [
    path("open/", OpenChatAPIView.as_view()),
    path("send/", SendMessageAPIView.as_view()),
    path(
        "conversation/<int:conversation_id>/messages/",
        MessageListAPIView.as_view()
    ),
    path("inbox/", InboxAPIView.as_view(), name="chat-inbox"),
]

