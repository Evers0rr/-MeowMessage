from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView, DetailView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q
from users.models import User
from .models import Subscribers, Friendship, Friendrequest
from notifications.models import Notification

class FriendsListView(LoginRequiredMixin, ListView):
    model = Friendship
    template_name = 'friends/friends_list.html'
    context_object_name = 'friendships'
    paginate_by = 5

    def get_queryset(self):
        return Friendship.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user)
        ).select_related('user1', 'user2').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        friendships = self.get_queryset()
        friends = []
        for friendship in friendships:
            friend = friendship.user2 if friendship.user1 == self.request.user else friendship.user1
            friends.append({
                'user': friend,
                'friendship': friendship,
                'friends_since': friendship.created_at
            })
        
        context['friends'] = friends
        context['friends_count'] = len(friends)
        
        return context


class SubscribeToggleView(LoginRequiredMixin, View):
    def post(self, request, username):
        profile_user = get_object_or_404(User, username=username)

        if request.user == profile_user:
            return JsonResponse({'error': 'Ви не можете підписатися на себе.'}, status=400)

        try:
            subscription = Subscribers.objects.filter(user=request.user, channel=profile_user).first()
            if subscription:
                subscription.delete()
                is_subscribed = False
                message = f"Ви відписалися від {profile_user.username}"
            else:
                Subscribers.objects.create(user=request.user, channel=profile_user)
                is_subscribed = True
                message = f"Ви підписалися на {profile_user.username}"


            return JsonResponse({
                'is_subscribed': is_subscribed,
                'subscribers_count': Subscribers.objects.filter(channel=profile_user).count(),
                'message': message,
                'success': True 
            })

        except (ValidationError, IntegrityError) as e:
            return JsonResponse({'error': str(e)}, status=400)


class FriendRequestView(LoginRequiredMixin, View):
    def post(self, request, username):
        receiver = get_object_or_404(User, username=username)

        if request.user == receiver:
            return JsonResponse({'error': 'Не можна надіслати запит самому собі'}, status=400)

        if Friendship.objects.filter(
            Q(user1=request.user, user2=receiver) | Q(user1=receiver, user2=request.user)
        ).exists():
            return JsonResponse({'error': 'Ви вже друзі з цим користувачем'}, status=400)

        existing_request = Friendrequest.objects.filter(sender=request.user, receiver=receiver).first()
        if existing_request:
            return JsonResponse({'error': 'Запит вже надіслано'}, status=400)

        reverse_request = Friendrequest.objects.filter(sender=receiver, receiver=request.user, accepted=False).first()
        if reverse_request:
            try:
                Friendship.objects.create(user1=request.user, user2=receiver)
                reverse_request.delete()

                Notification.objects.create(
                    recipient=receiver,
                    sender=request.user,
                    notification_type='friend_accept',
                    message=f"{request.user.username} прийняв ваш запит у друзі"
                )

                return JsonResponse({
                    'success': True,
                    'message': 'Запит прийнято, тепер ви друзі',
                    'is_friend': True
                })
            except (ValidationError, IntegrityError) as e:
                return JsonResponse({'error': str(e)}, status=400)

        try:
            friend_request = Friendrequest.objects.create(sender=request.user, receiver=receiver)

            Notification.objects.create(
                recipient=receiver,
                sender=request.user,
                notification_type='friend_request',
                friend_request=friend_request,
                message=f"{request.user.username} надіслав вам запит у друзі"
            )

            return JsonResponse({
                'success': True,
                'message': 'Запит у друзі надіслано',
                'request_sent': True
            })
        except (ValidationError, IntegrityError) as e:
            return JsonResponse({'error': str(e)}, status=400)


class FriendRequestActionView(LoginRequiredMixin, View):
    def post(self, request, request_id, action):
        friend_request = get_object_or_404(Friendrequest, id=request_id, receiver=request.user, accepted=False)

        try:
            if action == 'accept':
                Friendship.objects.create(user1=friend_request.sender, user2=friend_request.receiver)
                friend_request.delete()

                Notification.objects.create(
                    recipient=friend_request.sender,
                    sender=request.user,
                    notification_type='friend_accept',
                    message=f"{request.user.username} прийняв ваш запит у друзі"
                )

                return JsonResponse({'success': True, 'message': 'Запит у друзі прийнято', 'is_friend': True})

            elif action == 'reject':
                friend_request.delete()

                Notification.objects.create(
                    recipient=friend_request.sender,
                    sender=request.user,
                    notification_type='friend_reject',
                    message=f"{request.user.username} відхилив ваш запит у друзі"
                )

                return JsonResponse({'success': True, 'message': 'Запит у друзі відхилено'})

            else:
                return JsonResponse({'error': 'Невірна дія'}, status=400)
        except (ValidationError, IntegrityError) as e:
            return JsonResponse({'error': str(e)}, status=400)


class CancelFriendRequestView(LoginRequiredMixin, View):
    def post(self, request, request_id):
        friend_request = get_object_or_404(Friendrequest, id=request_id, sender=request.user, accepted=False)
        friend_request.delete()
        return JsonResponse({'success': True, 'message': 'Запит у друзі скасовано'})


class RemoveFriendView(LoginRequiredMixin, View):
    def post(self, request, username):
        target_user = get_object_or_404(User, username=username)
        friendship = Friendship.objects.filter(
            Q(user1=request.user, user2=target_user) |
            Q(user1=target_user, user2=request.user)
        ).first()

        if friendship:
            friendship.delete()


            return JsonResponse({
                'success': True,
                'message': f'Ви видалили {target_user.username} з друзів',
                'is_friend': False
            })
        else:
            return JsonResponse({'error': 'Дружби не існує'}, status=400)
