from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from .models import Post
from users.models import User

class PostListView(ListView):
    model = Post
    template_name = 'posts/post_list.html'
    context_object_name = 'friends_posts'
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Post.objects.none()

        friends_list = user.friends()
        friend_ids = [friend.id for friend in friends_list]

        return Post.objects.filter(
            author__id__in=friend_ids
        ).order_by('-created_at')[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['popular_users'] = User.objects.annotate(
            subscribers_count=Count('subscribers_to')
        ).order_by('-subscribers_count')[:5]

        if self.request.user.is_authenticated:
            context['debug_friends_count'] = len(self.request.user.friends())
        else:
            context['debug_friends_count'] = 0

        context['debug_posts_count'] = context['friends_posts'].count()
        context['group_posts'] = Post.objects.none()
        context['popular_events'] = []
        context['popular_communities'] = []

        return context