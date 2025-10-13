from django.urls import path
from .views import (
        PrivateChat,
        SendPrivateMessage,
        GroupChat,
        SendGroupMessage,
        GroupChatPage,
        PrivateChatPage,
)

app_name = "chat"

urlpatterns = [
    path("private/<str:username>/", PrivateChat.as_view(), name="private-chat-api"),
    path("private/<str:username>/send/", SendPrivateMessage.as_view(), name="send-private-message-api"),
    path("group/<int:chat_id>/", GroupChat.as_view(), name="group-chat-api"),
    path("group/<int:chat_id>/send/", SendGroupMessage.as_view(), name="send-group-message-api"),
    path("private/<str:username>/page/", PrivateChatPage.as_view(), name="private-chat-page"),
    path("group/<int:chat_id>/page/", GroupChatPage.as_view(), name="group-chat-page"),
]
