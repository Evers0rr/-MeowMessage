from django.urls import path
from .views import NotificationListView, mark_as_read

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('<int:notification_id>/read/', mark_as_read, name='mark_read'),
]