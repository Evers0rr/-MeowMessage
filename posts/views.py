from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DeleteView, View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from .models import Post, Comment, Like
from users.models import User
from groups.models import Group, GroupPost
from .forms import PostForm
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.http import Http404


class HomeView(ListView):
    model = Post
    template_name = 'posts/home.html'
    context_object_name = 'friends_posts'
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Post.objects.none()

        friends_list = user.friends()
        friend_ids = [friend.id for friend in friends_list]

        qs = Post.objects.filter(
            Q(author__id__in=friend_ids) &
            (Q(privacy_status="public") | Q(privacy_status="friends"))
        ).annotate(
            likes_count=Count('likes', filter=Q(likes__like_type='like')),
            dislikes_count=Count('likes', filter=Q(likes__like_type='dislike'))
        ).order_by('-created_at')[:5]

        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['popular_posts'] = (
            Post.objects.filter(privacy_status="public")
            .annotate(likes_count=Count("likes", filter=Q(likes__like_type="like")))
            .order_by("-likes_count", "-created_at")[:5]
        )

        context['popular_users'] = User.objects.annotate(
            subscribers_count=Count('subscribers_to')
        ).order_by('-subscribers_count')[:5]

        context['popular_groups'] = Group.objects.annotate(
            members_count=Count('members', distinct=True)
        ).order_by('-members_count')[:5]

        if user.is_authenticated:
            user_groups = user.members.all()
            context['group_posts'] = GroupPost.objects.filter(
                group__in=user_groups
            ).select_related('group', 'author').annotate(
                likes_count=Count('group_likes', filter=Q(group_likes__like_type='like')),
                dislikes_count=Count('group_likes', filter=Q(group_likes__like_type='dislike'))
            ).order_by('-created_at')[:5]
        else:
            context['group_posts'] = GroupPost.objects.none()

        return context

class PostsListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'posts/post_list.html'
    context_object_name = 'all_posts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        friends_ids = [friend.id for friend in user.friends()]
        context['friends_posts'] = (
            Post.objects.filter(
                author__id__in=friends_ids,
                privacy_status__in=['public', 'friends']
            )
            .select_related('author')
            .order_by('-created_at')[:3]
        )

        subscriptions_ids = [u.id for u in user.get_subscriptions()]
        context['subscriptions_posts'] = (
            Post.objects.filter(
                author__id__in=subscriptions_ids,
                privacy_status='public'
            )
            .select_related('author')
            .order_by('-created_at')[:3]
        )

        user_groups = user.members.all()
        context['group_posts'] = (
            GroupPost.objects.filter(group__in=user_groups)
            .select_related('group', 'author')
            .order_by('-created_at')[:3]
        )

        context['public_posts'] = (
            Post.objects.filter(privacy_status='public')
            .exclude(Q(author__id__in=friends_ids) | Q(author__id__in=subscriptions_ids))
            .select_related('author')
            .order_by('-created_at')[:3]
        )

        context['popular_posts'] = (
            Post.objects.filter(privacy_status='public')
            .annotate(likes_count=Count('likes', filter=Q(likes__like_type='like')))
            .order_by('-likes_count', '-created_at')[:5]
        )

        return context

class MyPostsView(LoginRequiredMixin, ListView):
    template_name = "posts/my_posts.html"
    context_object_name = "posts"
    paginate_by = 8

    def get_queryset(self):
        user = self.request.user

        type_filter = self.request.GET.get("type", "all")  
        sort_by = self.request.GET.get("sort", "date_desc") 

        user_posts = Post.objects.filter(author=user)
        group_posts = GroupPost.objects.filter(author=user)

        all_posts = list(user_posts) + list(group_posts)

        for post in all_posts:
            if isinstance(post, GroupPost):
                post.is_group_post = True
                post.post_type = "Груповий"
            else:
                post.is_group_post = False
                if post.privacy_status == "public":
                    post.post_type = "Публічний"
                elif post.privacy_status == "friends":
                    post.post_type = "Для друзів"
                elif post.privacy_status == "private":
                    post.post_type = "Приватний"
                else:
                    post.post_type = "Інший"
        

            post.likes_count = getattr(post, "get_likes_count", lambda: 0)() if hasattr(post, "get_likes_count") else getattr(post, "likes_count", 0)
            post.comments_count = getattr(post, "get_comments_count", lambda: 0)() if hasattr(post, "get_comments_count") else getattr(post, "comments_count", 0)

        if type_filter != "all":
            all_posts = [p for p in all_posts if p.post_type == type_filter]

        reverse = True
        if sort_by == "likes_asc":
            key_func = lambda p: p.likes_count
            reverse = False
        elif sort_by == "likes_desc":
            key_func = lambda p: p.likes_count
        elif sort_by == "comments_asc":
            key_func = lambda p: p.comments_count
            reverse = False
        elif sort_by == "comments_desc":
            key_func = lambda p: p.comments_count
        elif sort_by == "date_asc":
            key_func = lambda p: p.created_at
            reverse = False
        else:
            key_func = lambda p: p.created_at

        all_posts.sort(key=key_func, reverse=reverse)

        return all_posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Мої пости"
        context["post_count"] = len(context["posts"])
        context["type_filter"] = self.request.GET.get("type", "all")
        context["sort_by"] = self.request.GET.get("sort", "date_desc")
        return context

class CategoryPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'posts/category_posts.html'
    context_object_name = 'posts'
    paginate_by = 8

    def get_queryset(self):
        category = self.kwargs.get('category')
        user = self.request.user
        username = self.request.GET.get('username')

        qs = Post.objects.none()

        if category == 'friends':
            friend_ids = [f.id for f in user.friends()]
            qs = Post.objects.filter(
                author__id__in=friend_ids,
                privacy_status__in=['public', 'friends']
            )

        elif category == 'subscriptions':
            subscriptions_ids = [u.id for u in user.get_subscriptions()]
            qs = Post.objects.filter(
                author__id__in=subscriptions_ids,
                privacy_status='public'
            )
        

        elif category == 'groups':
            groups = user.members.all()
            qs = GroupPost.objects.filter(group__in=groups)

        elif category == 'public':
            qs = Post.objects.filter(privacy_status='public')

        elif category == 'private':
            qs = Post.objects.filter(author=user, privacy_status='private')

        if username:
            qs = qs.filter(author__username__icontains=username)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.kwargs.get('category')
        context['username_filter'] = self.request.GET.get('username', '')

        if context['posts'].exists():
            context['model_name'] = context['posts'].first().__class__.__name__
        else:
            context['model_name'] = "Post"

        return context


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        user = self.request.user

        if post.privacy_status == "friends" and user not in post.author.friends() and user != post.author:
            raise Http404("Пост не знайдено")
        if post.privacy_status == "private" and user != post.author:
            raise Http404("Пост не знайдено")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        user = self.request.user

        context['comments'] = post.comments.filter(parent_comment__isnull=True)\
                                .select_related("author")\
                                .prefetch_related('replies__author')\
                                .order_by('created_at')

        context['can_manage'] = (user == post.author)

        context['likes_count'] = post.get_likes_count()
        context['dislikes_count'] = post.get_dislikes_count()

        context['user_liked'] = post.likes.filter(user=user, like_type='like').exists()
        context['user_disliked'] = post.likes.filter(user=user, like_type='dislike').exists()

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        post = self.object
        user = request.user

        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent')

        if content:
            if len(content) > 500:
                messages.error(request, "Коментар не може перевищувати 500 символів")
                return redirect('posts:post-detail', pk=post.pk)

            try:
                comment = Comment(
                    post=post,
                    author=user,
                    content=content
                )
                if parent_id:
                    try:
                        parent_comment = Comment.objects.get(id=parent_id, post=post)
                        comment.parent_comment = parent_comment
                    except Comment.DoesNotExist:
                        pass

                comment.full_clean()
                comment.save()
                messages.success(request, "Коментар додано! ✅")
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
            except Exception as e:
                messages.error(request, f"Помилка при збереженні коментаря: {str(e)}")
        else:
            messages.error(request, "Коментар не може бути порожнім")

        return redirect('posts:post-detail', pk=post.pk)

# class PrivatePostDetailView(DetailView):   РЕАЛІЗУЮ ПОТІМ
#     model = Post
#     template_name = "posts/post_detail.html"
#     context_object_name = "post"

#     def get_object(self, queryset=None):
#         token = self.kwargs.get("token")
#         post = get_object_or_404(Post, private_token=token, privacy_status="private")
#         return post

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         post = self.object
#         context['comments'] = post.comments.filter(parent_comment__isnull=True)\
#                                 .select_related("author")\
#                                 .prefetch_related('replies__author')\
#                                 .order_by('created_at')

#         context['likes_count'] = post.get_likes_count()
#         context['dislikes_count'] = post.get_dislikes_count()
#         context['user_liked'] = self.request.user.is_authenticated and post.likes.filter(user=self.request.user, like_type='like').exists()
#         context['user_disliked'] = self.request.user.is_authenticated and post.likes.filter(user=self.request.user, like_type='dislike').exists()

#         return context


@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created and like.like_type == 'like':
        like.delete()
    else:
        like.like_type = 'like'
        like.save()
    return redirect('posts:post-detail', pk=pk)


@login_required
def dislike_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created and like.like_type == 'dislike':
        like.delete()
    else:
        like.like_type = 'dislike'
        like.save()
    return redirect('posts:post-detail', pk=pk)


class DeleteCommentView(LoginRequiredMixin, View):
    def post(self, request, post_pk, comment_pk):
        comment = get_object_or_404(Comment, pk=comment_pk, post_id=post_pk)
        post = get_object_or_404(Post, pk=post_pk)

        can_delete = (
            request.user == comment.author or
            request.user == post.author or
            request.user.is_superuser or
            request.user.is_staff
        )

        if not can_delete:
            messages.error(request, "У вас немає прав для видалення цього коментаря")
            return redirect('posts:post-detail', pk=post_pk)

        comment.delete()
        messages.success(request, "Коментар успішно видалено")
        return redirect('posts:post-detail', pk=post_pk)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "posts/post_confirm_delete.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return Post.objects.all()
        return Post.objects.filter(author=user)

    def get_success_url(self):
        messages.success(self.request, "Пост успішно видалено")
        return reverse_lazy('posts:posts-list')


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/create_post.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Пост успішно створено!")
        return response

    def get_success_url(self):
        return reverse('posts:posts-list')
