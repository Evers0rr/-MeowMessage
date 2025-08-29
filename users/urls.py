from django.urls import path
from .views import RegisterView, LoginView, CustomLogoutView, SettingsView, ClearAvatarView, activate_account, confirm_new_email, ProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path("clear-avatar/", ClearAvatarView.as_view(), name="clear_avatar"),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('confirm-email/<uidb64>/<token>/<encoded_email>/', confirm_new_email, name='confirm_new_email'),
    path('<str:username>/', ProfileView.as_view(), name="profile"),
]