from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from posts.models import Post, Comment
from groups.models import GroupInvitation
from friends.models import Friendrequest
from feedback.models import Feedback
from django.urls import reverse
# Create your models here.

NOTIFICATION_TYPE_CHOICES = [
    ('comment', 'Коментар'),
    ('friend_request', 'Запит на дружбу'),
    ('friend_accept', 'Прийняття запиту на дружбу'),
    ('group_invitation', 'Запрошення до групи'),
    ('feedback', 'Відгук'),
]

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications', blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    friend_request = models.ForeignKey(Friendrequest, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    group_invitation = models.ForeignKey(GroupInvitation, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, default='')

    def clean(self):
        if self.notification_type == 'comment' and not self.comment:
            raise ValidationError("Коментар повинен бути вказаний для типу 'comment'.")
        if self.notification_type == 'friend_request' and not self.friend_request:
            raise ValidationError("Запит на дружбу повинен бути вказаний для типу 'friend_request'.")
        if self.notification_type == 'group_invitation' and not self.group_invitation:
            raise ValidationError("Запрошення до групи повинно бути вказане для типу 'group_invitation'.")
        if self.notification_type == 'feedback' and not self.feedback:
            raise ValidationError("Відгук повинен бути вказаний для типу 'feedback'.")
        if self.notification_type not in dict(NOTIFICATION_TYPE_CHOICES).keys():
            raise ValidationError("Недійсний тип сповіщення.")
        if self.sender == self.recipient:
            raise ValidationError("Відправник і отримувач не можуть бути однаковими.")
        
    def get_absolute_url(self):
        if self.notification_type == 'friend_request':
            return reverse('friends:invites')
        elif self.notification_type == 'comment':
            if self.comment and self.comment.post:
                return reverse('posts:detail', args=[self.comment.post.id])
            elif self.comment and self.comment.group_post:
                return reverse('groups:post_detail', args=[self.comment.group_post.id])
            return '#'   
        elif self.notification_type == 'group_invitation':
            return reverse('groups:invitations')
        elif self.notification_type == 'feedback':
            return reverse('feedback:list')
        else:
            return '#'
        
    def get_message(self):
        if self.notification_type == 'friend_request':
            return f"{self.sender} надіслав вам запит на дружбу."
        elif self.notification_type == 'friend_accept':
            return f"{self.sender} прийняв ваш запит на дружбу."
        elif self.notification_type == 'comment':
            return f"{self.sender} прокоментував ваш пост."
        elif self.notification_type == 'group_invitation' and self.group_invitation:
            return f"{self.sender} запросив вас до групи {self.group_invitation.group.name}."
        elif self.notification_type == 'feedback':
            return f"{self.sender} залишив відгук."
        else:
            return "У вас нове сповіщення."
          
    def __str__(self):
        return f"Сповіщення для {self.recipient} від {self.sender} | Тип: {self.notification_type} | Прочитано: {self.is_read} | Дата створення: {self.created_at}"
    
    class Meta:
        verbose_name = 'Сповіщення'
        verbose_name_plural = 'Сповіщення'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]
    def mark_as_read(self):
        self.is_read = True
        self.save()
    


