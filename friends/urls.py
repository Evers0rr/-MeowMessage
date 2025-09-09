from django.urls import path
from .views import SubscribeToggleView, FriendRequestView, FriendRequestActionView, CancelFriendRequestView, RemoveFriendView

app_name = 'friends'

urlpatterns = [
    path('subscribe/<str:username>/',SubscribeToggleView.as_view(),name='toggle_subscribe'),
    path('request/<str:username>/', FriendRequestView.as_view(), name='friend_request'),
    path('request/<int:request_id>/<str:action>/', FriendRequestActionView.as_view(), name='friend_request_action'),
    path('request/cancel/<int:request_id>/', CancelFriendRequestView.as_view(), name='cancel_friend_request'),
    path('remove/<str:username>/', RemoveFriendView.as_view(), name='remove_friend'),

]