from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import PrivateMessage, GroupChat, GroupMessage


User = get_user_model()


class PrivateChat(LoginRequiredMixin, View):
    def get(self, request, username):
        other_user = get_object_or_404(User, username=username)

        messages = PrivateMessage.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user)
        ).order_by("created_at")

        data = [
            {
                "id": msg.id,
                "sender": msg.sender.username,
                "receiver": msg.receiver.username,
                "text": msg.text,
                "file": msg.file.url if msg.file else "",
                "content_type": msg.content_type,
                "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for msg in messages
        ]
        return JsonResponse({"messages": data})


class SendPrivateMessage(LoginRequiredMixin, View):
    def post(self, request, username):
        receiver = get_object_or_404(User, username=username)
        text = request.POST.get("text", "")
        file = request.FILES.get("file")
        content_type = request.POST.get("content_type", "text")

        msg = PrivateMessage(
            sender=request.user,
            receiver=receiver,
            text=text,
            file=file,
            content_type=content_type,
        )
        try:
            msg.clean()
            msg.save()
            return JsonResponse(
                {
                    "success": True,
                    "id": msg.id,
                    "text": msg.text,
                    "file": msg.file.url if msg.file else "",
                    "content_type": msg.content_type,
                    "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M"),
                    "sender": msg.sender.username,
                }
            )
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)


class GroupChat(LoginRequiredMixin, View):
    def get(self, request, chat_id):
        chat = get_object_or_404(GroupChat, id=chat_id)

        if request.user not in chat.members.all():
            return JsonResponse({"error": "Ви не учасник цього чату"}, status=403)

        messages = chat.messages.all().order_by("created_at")
        data = [
            {
                "id": msg.id,
                "sender": msg.sender.username,
                "text": msg.text,
                "file": msg.file.url if msg.file else "",
                "content_type": msg.content_type,
                "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for msg in messages
        ]
        return JsonResponse({"messages": data})


class SendGroupMessage(LoginRequiredMixin, View):
    def post(self, request, chat_id):
        chat = get_object_or_404(GroupChat, id=chat_id)

        if request.user not in chat.members.all():
            return JsonResponse({"error": "Ви не учасник цього чату"}, status=403)

        text = request.POST.get("text", "")
        file = request.FILES.get("file")
        content_type = request.POST.get("content_type", "text")

        msg = GroupMessage(
            chat=chat,
            sender=request.user,
            text=text,
            file=file,
            content_type=content_type,
        )
        try:
            msg.clean()
            msg.save()
            return JsonResponse(
                {
                    "success": True,
                    "id": msg.id,
                    "text": msg.text,
                    "file": msg.file.url if msg.file else "",
                    "content_type": msg.content_type,
                    "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M"),
                    "sender": msg.sender.username,
                }
            )
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)


class GroupChatPage(LoginRequiredMixin, TemplateView):
    template_name = "chat/chat_box.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat = get_object_or_404(GroupChat, id=self.kwargs["chat_id"])

        if self.request.user not in chat.members.all():
            raise PermissionError("Ви не учасник цього чату")

        context["chat_type"] = "group"
        context["chat"] = chat
        context["username"] = self.request.user.username
        context["messages"] = chat.messages.all().order_by("created_at")
        return context


class PrivateChatPage(View):
    def get(self, request, username):
        other_user = get_object_or_404(User, username=username)
        messages = PrivateMessage.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user)
        ).order_by("created_at")

        for msg in messages:
            if msg.file:
                ext = msg.file.url.lower()
                msg.is_image = ext.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
                msg.is_video = ext.endswith((".mp4", ".mov", ".avi", ".webm"))
            else:
                msg.is_image = msg.is_video = False

        context = {
            "messages": messages,
            "chat_type": "private",
            "chat": other_user,
        }
        return render(request, "chat/chat_box.html", context)



