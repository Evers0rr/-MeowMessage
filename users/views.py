from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import DetailView
from django.db.models import Q
from django.utils import timezone
from .forms import CustomUserCreationForm, ProfileSettingsForm
from .models import User
from posts.models import Post
from groups.models import Group
from friends.models import Friendship, Subscribers, Friendrequest, Friendship
from groups.models import Group

ALERT_TEMPLATE = 'base/alert.html'
EMAIL_CONFIRM_TEMPLATE = 'users/email_confirm.html'
REGISTER_TEMPLATE = 'users/register.html'
LOGIN_TEMPLATE = 'users/login.html'
SETTINGS_TEMPLATE = 'users/settings.html'

class RegisterView(UserPassesTestMixin, View):

    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, REGISTER_TEMPLATE, {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://127.0.0.1:8000/users/activate/{uid}/{token}/"

            send_mail(
                subject="Підтвердження акаунту",
                message=(
                    f"Привіт {user.username}!\n\n"
                    f"Щоб активувати акаунт, перейдіть за посиланням:\n{activation_link}\n\n"
                    f"Якщо ви не реєструвалися, просто проігноруйте це повідомлення."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return render(request, ALERT_TEMPLATE, {
                'message': "Реєстрація пройшла успішно! Лист для активації відправлено.",
                'redirect_url': reverse_lazy('login')
            })

    
        return render(request, REGISTER_TEMPLATE, {'form': form})

    def test_func(self):
        return not self.request.user.is_authenticated

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, ALERT_TEMPLATE, {
            'message': "Користувач уже видалено або посилання недійсне.",
            'redirect_url': reverse_lazy('home')
        })

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, ALERT_TEMPLATE, {
            'message': "Акаунт успішно активовано! Ви авторизовані.",
            'redirect_url': reverse_lazy('home')
        })
    else:
        return render(request, ALERT_TEMPLATE, {
            'message': "Посилання для активації недійсне або прострочене.",
            'redirect_url': reverse_lazy('home')
        })

class LoginView(UserPassesTestMixin, View):

    def get(self, request):
        form = AuthenticationForm()
        return render(request, LOGIN_TEMPLATE, {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return render(request, ALERT_TEMPLATE, {
                'message': "Вхід успішний!",
                'redirect_url': reverse_lazy('home')
            })
        return render(request, LOGIN_TEMPLATE, {'form': form})

    def test_func(self):
        return not self.request.user.is_authenticated



class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        return render(request, ALERT_TEMPLATE, {
            'message': "Ви успішно вийшли з акаунту.",
            'redirect_url': str(self.next_page)
        })
    
class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        context['posts'] = Post.objects.filter(author=user).order_by('-created_at')[:10]

        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        context['friends'] = [fs.user2 if fs.user1 == user else fs.user1 for fs in friendships][:12]
        context['friends_count'] = friendships.count()

        context['subscribers_count'] = Subscribers.objects.filter(channel=user).count()
        context['subscriptions_count'] = Subscribers.objects.filter(user=user).count()

        context['groups'] = user.members.all().order_by('-created_at')
        context['groups_count'] = context['groups'].count()

        context['is_own_profile'] = self.request.user == user

        if not context['is_own_profile']:
            context['is_subscribed'] = Subscribers.objects.filter(
                user=self.request.user,
                channel=user
            ).exists()

            context['is_friend'] = Friendship.objects.filter(
                Q(user1=self.request.user, user2=user) |
                Q(user1=user, user2=self.request.user)
            ).exists()

            sent_request = Friendrequest.objects.filter(
                sender=self.request.user,
                receiver=user,
                accepted=False
            ).first()

            received_request = Friendrequest.objects.filter(
                sender=user,
                receiver=self.request.user,
                accepted=False
            ).first()

            context['friend_request_sent'] = bool(sent_request)
            context['friend_request_received'] = bool(received_request)

            if sent_request:
                context['sent_request_id'] = sent_request.id
            if received_request:
                context['received_request_id'] = received_request.id

            if context['is_friend']:
                context['friend_status'] = 'remove'
            elif context['friend_request_sent']:
                context['friend_status'] = 'pending'
            else:
                context['friend_status'] = 'add'

        else:
            context['is_subscribed'] = False
            context['is_friend'] = False
            context['friend_request_sent'] = False
            context['friend_request_received'] = False
            context['friend_status'] = 'add'

        return context

class SettingsView(LoginRequiredMixin, View):

    def get(self, request):
        form = ProfileSettingsForm(instance=request.user)
        return render(request, SETTINGS_TEMPLATE, {'form': form})

    def post(self, request):
        form = ProfileSettingsForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)

            new_email = form.cleaned_data.get('new_email')
            if new_email and new_email != user.email:
                user.new_email = new_email
                user.new_email_at = timezone.now()
                user.save(update_fields=['new_email'])

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                encoded_email = urlsafe_base64_encode(force_bytes(new_email))
                confirm_link = f"http://127.0.0.1:8000/users/confirm-email/{uid}/{token}/{encoded_email}/"

                send_mail(
                    subject="Підтвердження зміни пошти",
                    message=f"Привіт {user.username}!\nЩоб підтвердити нову пошту, перейдіть за посиланням:\n{confirm_link}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[new_email],
                )

                return render(request, ALERT_TEMPLATE, {
                    'message': "Лист на підтвердження нової пошти відправлено!",
                    'redirect_url': request.path
                })
            user.save()
            return render(request, ALERT_TEMPLATE, {
                'message': "Зміни профілю збережено!",
                'redirect_url': request.path
            })
        return render(request, SETTINGS_TEMPLATE, {'form': form})

def confirm_new_email(request, uidb64, token, encoded_email):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        new_email = force_str(urlsafe_base64_decode(encoded_email))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, EMAIL_CONFIRM_TEMPLATE, {
            'message': "Токен недійсний або посилання прострочене.",
            'redirect_url': '/'
        })

    if user.new_email and default_token_generator.check_token(user, token):
        user.email = new_email
        user.new_email = None
        user.save(update_fields=['email', 'new_email'])
        return render(request, EMAIL_CONFIRM_TEMPLATE, {
            'message': "Електронну пошту успішно змінено!",
            'redirect_url': '/'
        })

    if user.new_email is None:
        return render(request, EMAIL_CONFIRM_TEMPLATE, {
            'message': "Посилання вже використано або email скинуто.",
            'redirect_url': '/'
        })

    return render(request, EMAIL_CONFIRM_TEMPLATE, {
        'message': "Токен недійсний або посилання прострочене.",
        'redirect_url': '/'
    })


class ClearAvatarView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if user.avatar and user.avatar.name != "avatars/default.jpg":
            user.avatar.delete(save=False)
        user.avatar = "avatars/default.jpg"
        user.save(update_fields=["avatar"])
        return JsonResponse({"success": True, "default_avatar_url": "/media/avatars/default.jpg"})
    

class ClearCoverView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.cover_image:
            user.cover_image.delete(save=False)
            user.cover_image = None
        user.save(update_fields=["cover_image"])
        return JsonResponse({"success": True})

