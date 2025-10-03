from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View, TemplateView, FormView , CreateView, DetailView, DeleteView
from .models import Group, MemberShip, GroupCategory, GroupPost, GroupComment, GroupJoinRequest, GroupInvitation, GroupLike
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from notifications.models import Notification
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .forms import GroupCreateForm, GroupPostForm, GroupCommentForm, GroupInvitationForm
from django.urls import reverse_lazy
from django.apps import apps
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied



# Create your views here.
class GroupListView(ListView):
    model = Group
    template_name = 'groups/group_list.html'
    context_object_name = 'groups'
    paginate_by = 10

    def get_queryset(self):
        qs = Group.objects.all().select_related("category")
        category_id = self.request.GET.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        privacy = self.request.GET.get("privacy")
        if privacy in ["public", "private"]:
            qs = qs.filter(public_or_private=privacy)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = GroupCategory.objects.all()
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_privacy"] = self.request.GET.get("privacy", "")
        return context

        
class MyGroupsListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'groups/my_groups.html'
    context_object_name = 'groups'
    paginate_by = 10

    def get_queryset(self):
        qs = Group.objects.filter(memberships__user=self.request.user).select_related('category')
        category_id = self.request.GET.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        privacy = self.request.GET.get("privacy")
        if privacy in ["public", "private"]:
            qs = qs.filter(public_or_private=privacy)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = GroupCategory.objects.all()
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_privacy"] = self.request.GET.get("privacy", "")
        return context

    
class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupCreateForm
    template_name = "groups/group_create.html"
    success_url = reverse_lazy('groups:my-groups')

    def form_valid(self, form):
        group = form.save(commit=False)

        group.owner = self.request.user
        group.save()
        MemberShip.objects.create(group=group, user=self.request.user, role='owner')
        group.members.add(self.request.user)

        return super().form_valid(form)
    
class GroupDetailView(DetailView):
    model = Group
    template_name = 'groups/group_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        group = self.get_object()

        context['is_member'] = False
        context['is_owner'] = False
        context['is_admin'] = False
        context['is_moderator'] = False
        context['can_join'] = False

        if user.is_authenticated:
            membership = MemberShip.objects.filter(user=user, group=group).first()
            if membership:
                context['is_member'] = True
                role = membership.role.lower() if membership.role else ""
                if role == "owner":
                    context['is_owner'] = True
                elif role == "admin":
                    context['is_admin'] = True
                elif role == "moderator":
                    context['is_moderator'] = True

            context['can_join'] = group.public_or_private == 'public' and not context['is_member']

        memberships = MemberShip.objects.filter(group=group).select_related("user")
        role_priority = {"owner": 1, "admin": 2, "moderator": 3, "member": 4}
        sorted_memberships = sorted(memberships, key=lambda m: role_priority.get((m.role or "").lower(), 99))
        context["memberships"] = sorted_memberships

        return context

class GroupManageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "groups/group_manage.html"

    def test_func(self):
        group = get_object_or_404(Group, pk=self.kwargs["pk"])
        return MemberShip.objects.filter(group=group, user=self.request.user).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(Group, pk=self.kwargs["pk"])
        membership = MemberShip.objects.filter(group=group, user=self.request.user).first()

        context["group"] = group
        context["membership"] = membership
        context["is_admin"] = membership and membership.role in ["owner", "admin"]
        context["is_moderator"] = membership and membership.role in ["owner", "admin", "moderator"]

        memberships = MemberShip.objects.filter(group=group).select_related("user")
        role_priority = {"owner": 1, "admin": 2, "moderator": 3, "member": 4}
        sorted_memberships = sorted(memberships, key=lambda m: role_priority.get((m.role or "").lower(), 99))
        context["memberships"] = sorted_memberships

        return context
    
class GroupActivityView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = "groups/group.html"
    context_object_name = "group"

    def get_object(self):
        return get_object_or_404(Group, pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context["posts"] = GroupPost.objects.filter(group=group).order_by("-created_at")[:6]
        return context
    
class GroupPostsView(LoginRequiredMixin, ListView):
    model = GroupPost
    template_name = "groups/group_posts.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self):
        group = get_object_or_404(Group, pk=self.kwargs['pk'])
        return GroupPost.objects.filter(group=group).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = get_object_or_404(Group, pk=self.kwargs['pk'])
        return context
    
    
class GroupPostDetailView(LoginRequiredMixin, DetailView):
    model = GroupPost
    template_name = "groups/group_post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        group = get_object_or_404(Group, pk=self.kwargs['group_pk'])
        return GroupPost.objects.filter(group=group)

    def get_object(self, queryset=None):
        if hasattr(self, 'object'):
            return self.object
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(Group, pk=self.kwargs['group_pk'])
        post = self.get_object()
        
        context['group'] = group
        context['comments'] = post.comments.filter(parent__isnull=True)\
                                       .select_related("author")\
                                       .prefetch_related('replies__author')\
                                       .order_by('created_at')

        membership = None
        can_manage = False
        if self.request.user.is_authenticated:
            membership = group.memberships.filter(user=self.request.user).first()
            if membership and membership.role in ["moderator", "admin", "owner"]:
                can_manage = True

        context['membership'] = membership
        context['can_manage'] = can_manage

        context['groups_likes_count'] = post.group_likes.filter(like_type='like').count()
        context['groups_dislikes_count'] = post.group_likes.filter(like_type='dislike').count()
        
        user_like = post.group_likes.filter(user=self.request.user).first()
        context['user_liked'] = user_like.like_type == 'like' if user_like else False
        context['user_disliked'] = user_like.like_type == 'dislike' if user_like else False
    
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        post = self.object
        group = get_object_or_404(Group, pk=self.kwargs['group_pk'])
        
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent')
        
        if content:
            if len(content) > 500:
                messages.error(request, "Коментар не може перевищувати 500 символів")
                return redirect('groups:group-post-detail', group_pk=group.pk, pk=post.pk)
            
            try:
                comment = GroupComment(
                    post=post,
                    author=request.user,
                    content=content
                )
                
                if parent_id:
                    try:
                        parent_comment = GroupComment.objects.get(id=parent_id, post=post)
                        comment.parent = parent_comment
                    except GroupComment.DoesNotExist:
                        pass
                
                comment.full_clean()
                comment.save()
                messages.success(request, "Коментар додано!")
                
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
            except Exception as e:
                messages.error(request, f"Помилка при збереженні коментаря: {str(e)}")
        else:
            messages.error(request, "Коментар не може бути порожнім")
        
        return redirect('groups:group-post-detail', group_pk=group.pk, pk=post.pk)

@login_required
def like_group_post(request, pk, group_pk):
    post = get_object_or_404(GroupPost, pk=pk, group_id=group_pk)
    like, created = GroupLike.objects.get_or_create(post=post, user=request.user)

    if not created and like.like_type == 'like':
        like.delete()
    else:
        like.like_type = 'like'
        like.save()
    return redirect('groups:group-post-detail', group_pk=group_pk, pk=pk)


@login_required
def dislike_group_post(request, pk, group_pk):
    post = get_object_or_404(GroupPost, pk=pk, group_id=group_pk)
    like, created = GroupLike.objects.get_or_create(post=post, user=request.user)

    if not created and like.like_type == 'dislike':
        like.delete()
    else:
        like.like_type = 'dislike'
        like.save()
    return redirect('groups:group-post-detail', group_pk=group_pk, pk=pk)

class DeleteCommentView(LoginRequiredMixin, View):
    def post(self, request, group_pk, post_pk, comment_pk):
        comment = get_object_or_404(GroupComment, pk=comment_pk, post_id=post_pk)
        post = get_object_or_404(GroupPost, pk=post_pk, group_id=group_pk)
        group = get_object_or_404(Group, pk=group_pk)
        
        can_delete = (
            request.user == comment.author or 
            request.user == post.author or 
            self._can_manage_group(request.user, group)
        )
        
        if not can_delete:
            messages.error(request, "У вас немає прав для видалення цього коментаря")
            return redirect('groups:group-post-detail', group_pk=group_pk, pk=post_pk)
        
        comment.delete()
        messages.success(request, "Коментар успішно видалено")
        
        return redirect('groups:group-post-detail', group_pk=group_pk, pk=post_pk)
    
    def _can_manage_group(self, user, group):
        try:
            membership = group.memberships.get(user=user)
            return membership.role in ['moderator', 'admin', 'owner']
        except:
            return False

class CreateGroupPostView(LoginRequiredMixin, CreateView):
    model = GroupPost
    form_class = GroupPostForm
    template_name = "groups/create_post.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        group = get_object_or_404(Group, pk=self.kwargs['pk'])
        form.instance.group = group
        form.instance.author = self.request.user
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = get_object_or_404(Group, pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse_lazy('groups:group-posts', kwargs={'pk': self.kwargs['pk']})
    

class GroupPostDeleteView(DeleteView):
    model = GroupPost
    template_name = "groups/group_post_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy('groups:group-posts', kwargs={'pk': self.object.group.pk})

class ToggleMembershipView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        group = get_object_or_404(Group, id=self.kwargs['pk'])
        user = request.user
        membership = MemberShip.objects.filter(user=user, group=group).first()

        if membership:
            if membership.role == "owner":
                return JsonResponse({"status": "error", "message": "Власник не може покинути групу!"})
            membership.delete()
            group.members.remove(user)
            return JsonResponse({'status': 'left'})
        else:
            if group.public_or_private == 'private':
                if not GroupJoinRequest.objects.filter(user=user, group=group, status='pending').exists():
                    GroupJoinRequest.objects.create(user=user, group=group)
                return JsonResponse({'status': 'requested'})
            else:
                group.members.add(user)
                MemberShip.objects.create(user=user, group=group, role='member')
                return JsonResponse({'status': 'joined'})

@login_required
def toggle_membership(request, pk):
    group = get_object_or_404(Group, pk=pk)
    membership = MemberShip.objects.filter(group=group, user=request.user).first()

    if membership:
        if membership.role == "owner":
            return JsonResponse({"status": "error", "message": "Власник не може покинути групу!"})
        membership.delete()
        return JsonResponse({"status": "left"})
    else:
        if group.public_or_private == "public":
            MemberShip.objects.create(group=group, user=request.user, role="member")
            return JsonResponse({"status": "joined"})
        else:
            if not GroupJoinRequest.objects.filter(user=request.user, group=group, status='pending').exists():
                GroupJoinRequest.objects.create(user=request.user, group=group)
            return JsonResponse({"status": "requested"})


class GroupRequestsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "groups/group_requests.html"

    def test_func(self):
        group = get_object_or_404(Group, pk=self.kwargs["pk"])
        membership = MemberShip.objects.filter(group=group, user=self.request.user).first()
        return membership and membership.role in ["owner", "admin", "moderator"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(Group, pk=self.kwargs["pk"])
        context["group"] = group
        context["requests"] = GroupJoinRequest.objects.filter(group=group, status="pending").select_related("user").order_by("requested_at")
        membership = MemberShip.objects.filter(group=group, user=self.request.user).first()
        context["user_role"] = membership.role if membership else None
        return context


class GroupRequestActionView(LoginRequiredMixin, View):
    def post(self, request, pk, request_id):
        group = get_object_or_404(Group, pk=pk)
        membership = MemberShip.objects.filter(group=group, user=request.user).first()
        if not membership or membership.role not in ["owner", "admin", "moderator"]:
            return JsonResponse({"status": "forbidden"}, status=403)

        join_request = get_object_or_404(GroupJoinRequest, pk=request_id, group=group)

        action = request.POST.get("action") or request.headers.get("X-Action")
        if action not in ["accept", "reject"]:
            return JsonResponse({"status": "error", "message": "Невідома дія"}, status=400)

        if action == "accept":
            if not group.members.filter(id=join_request.user.id).exists():
                group.members.add(join_request.user)
            if not MemberShip.objects.filter(group=group, user=join_request.user).exists():
                MemberShip.objects.create(group=group, user=join_request.user, role="member")
            join_request.status = "accepted"
            join_request.save()

            try:
                Notification.objects.create(
                    recipient=join_request.user,
                    actor=request.user,
                    verb=f"Ваш запит до групи '{group.name}' прийнято",
                )
            except Exception:
                pass

            return JsonResponse({"status": "accepted", "user": join_request.user.username})

        else:
            join_request.status = "declined"
            join_request.save()

            try:
                Notification.objects.create(
                    recipient=join_request.user,
                    actor=request.user,
                    verb=f"Ваш запит до групи '{group.name}' відхилено",
                )
            except Exception:
                pass

            return JsonResponse({"status": "declined", "user": join_request.user.username})
        
ROLE_PRIORITIES = {
    "owner": 3,
    "admin": 2,
    "moderator": 1,
    "member": 0,
}


class GroupRolesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "groups/group_roles.html"

    def test_func(self):
        group = get_object_or_404(Group, pk=self.kwargs["pk"])
        membership = MemberShip.objects.filter(group=group, user=self.request.user).first()
        return membership and membership.role in ["owner", "admin"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(Group, pk=self.kwargs["pk"])
        membership = MemberShip.objects.filter(group=group, user=self.request.user).first()

        memberships = MemberShip.objects.filter(group=group).select_related("user")
        sorted_memberships = sorted(
            memberships,
            key=lambda m: ROLE_PRIORITIES.get(m.role, -1),
            reverse=True
        )

        members_data = []
        for m in sorted_memberships:
            members_data.append({
                "membership": m,
                "priority": ROLE_PRIORITIES.get(m.role, -1),
            })

        context["group"] = group
        context["members_data"] = members_data
        context["user_role"] = membership.role if membership else None
        context["user_priority"] = ROLE_PRIORITIES.get(membership.role, -1) if membership else -1

        return context


@login_required
def update_role(request, pk, user_id):
    group = get_object_or_404(Group, pk=pk)
    membership = MemberShip.objects.filter(group=group, user=request.user).first()

    if not membership or membership.role not in ["owner", "admin"]:
        return JsonResponse({"status": "forbidden"}, status=403)

    target_membership = get_object_or_404(MemberShip, group=group, user__id=user_id)
    new_role = request.POST.get("role")

    if new_role not in ["owner", "admin", "moderator", "member"]:
        return JsonResponse({"status": "error", "message": "Невідома роль"}, status=400)

    if target_membership.role == "owner" and membership.role != "owner":
        return JsonResponse({"status": "error", "message": "Ви не можете змінити роль власника"}, status=400)


    if target_membership.role == "owner" and new_role != "owner":
        owners_count = MemberShip.objects.filter(group=group, role="owner").count()
        if owners_count <= 1:
            return JsonResponse({"status": "error", "message": "Неможливо забрати роль у єдиного власника групи"}, status=400)

    target_membership.role = new_role
    target_membership.save()

    return JsonResponse({"status": "success", "user": target_membership.user.username, "role": new_role})

class KickMemberView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Ви повинні увійти"}, status=403)

        group = get_object_or_404(Group, pk=pk)
        membership = MemberShip.objects.filter(group=group, user=request.user).first()
        target_membership = get_object_or_404(MemberShip, group=group, user__id=user_id)

        if not membership:
            return JsonResponse({"status": "forbidden"}, status=403)

        if ROLE_PRIORITIES.get(membership.role, 0) <= ROLE_PRIORITIES.get(target_membership.role, 0):
            return JsonResponse({
                "status": "error", 
                "message": "Ви не можете вигнати цього користувача"
            }, status=400)

        if target_membership.role == "owner":
            return JsonResponse({
                "status": "error", 
                "message": "Неможливо вигнати власника"
            }, status=400)

        username = target_membership.user.username
        target_membership.delete()
        group.members.remove(target_membership.user)

        return JsonResponse({
            "status": "success",
            "message": f"Користувача {username} вигнано",
            "user_id": user_id
        })
    

class GroupInvitationView(LoginRequiredMixin, FormView):
    template_name = 'groups/group_invitation.html'
    form_class = GroupInvitationForm

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=self.kwargs['pk'])
        membership = MemberShip.objects.filter(group=self.group, user=request.user).first()

        if self.group.public_or_private == 'private' and (not membership or membership.role not in ['moderator', 'admin', 'owner']):
            return HttpResponseForbidden("У вас немає прав для запрошення користувачів.")

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group 
        return context

    def form_valid(self, form):
        invitee = form.cleaned_data['username']

        if self.group.members.filter(id=invitee.id).exists():
            return JsonResponse({
                'success': False,
                'error': "Цей користувач вже є учасником групи."
            })

        if GroupInvitation.objects.filter(invitee=invitee, group=self.group, status='pending').exists():
            return JsonResponse({
                'success': False,
                'error': "Запрошення цьому користувачу вже відправлене."
            })

        invitation = GroupInvitation.objects.create(
            inviter=self.request.user,
            invitee=invitee,
            group=self.group
        )

        Notification.objects.create(
            recipient=invitee,
            sender=self.request.user,
            notification_type='group_invitation',
            group_invitation=invitation
        )

        return JsonResponse({
            'success': True,
            'message': f"Запрошення {invitee.username} до групи {self.group.name} пройшло успішно!"
        })

    def get_success_url(self):
        return reverse_lazy('groups:group-activity', kwargs={'pk': self.group.pk})


class AcceptGroupInvitationView(LoginRequiredMixin, View):
    def post(self, request, invitation_id):
        invitation = get_object_or_404(GroupInvitation, pk=invitation_id, status='pending')

        if invitation.invitee != request.user:
            return JsonResponse({'success': False, 'error': "Це не ваше запрошення"}, status=403)

        MemberShip.objects.get_or_create(
            user=request.user,
            group=invitation.group,
            defaults={"role": "member"}
        )

        invitation.status = 'accepted'
        invitation.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f"Ви приєдналися до групи {invitation.group.name}"
        })


class DeclineGroupInvitationView(LoginRequiredMixin, View):
    def post(self, request, invitation_id):
        invitation = get_object_or_404(GroupInvitation, pk=invitation_id, status='pending')

        if invitation.invitee != request.user:
            return JsonResponse({'success': False, 'error': "Це не ваше запрошення"}, status=403)

        invitation.status = 'declined'
        invitation.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f"Ви відхилили запрошення до групи {invitation.group.name}"
        })