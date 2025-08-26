from django.db import models
from django.conf import settings
from friends.models import Friendship
from django.db.models import Q
from django.core.exceptions import ValidationError
# Create your models here.

CONTENT_TYPES = [
    ('text', 'Текст'),
    ('image', 'Зображення'),
    ('video', 'Відео'),
    ('file', 'Файл'),
]


class GroupChat(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name Group Chat')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='group_chats', verbose_name='Members')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')
    avatar = models.ImageField(upload_to='group_avatars/', blank=True, null=True, verbose_name='Avatar')
    description = models.TextField(blank=True, verbose_name='Description')

    def __str__(self):
        return f"{self.name} ({self.members.count()} учасників)"

    class Meta:
        verbose_name = 'Груповий чат'
        verbose_name_plural = 'Групові чати'
        ordering = ['-created_at']


class GroupMessage(models.Model):
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_messages')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='text')
    text = models.TextField(blank=True)
    file = models.FileField(upload_to='group_chat_files/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.text or self.file.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        import os

        if self.content_type == 'text':
            if not self.text.strip():
                raise ValidationError("Для текстового повідомлення потрібен текст.")
            if self.file:
                raise ValidationError("Текстове повідомлення не може містити файл.")
            
        if self.content_type == 'image':
            if not self.file:
                raise ValidationError("Для зображення потрібен файл.")
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext not in ['.png', '.jpg', '.jpeg', '.gif']:
                raise ValidationError("Неправильний формат файлу для зображення. Використовуйте PNG, JPG, JPEG або GIF.")

        if self.content_type == 'video':
            if not self.file:
                raise ValidationError("Для відео потрібен файл.")
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext not in ['.mp4', '.mov', '.avi', '.mkv']:
                raise ValidationError("Неправильний формат файлу для відео. Використовуйте MP4, MOV, AVI або MKV.")

        if self.content_type == 'file':
            if not self.file:
                raise ValidationError("Для повідомлення з файлом потрібно завантажити файл.")
    


    class Meta:
        ordering = ['created_at']
        verbose_name = 'Повідомлення у групі'
        verbose_name_plural = 'Повідомлення у групах'


class PrivateMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='text')
    text = models.TextField(blank=True)
    file = models.FileField(upload_to='private_chat_files/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.text or self.file.name}"
       
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Приватне повідомлення'
        verbose_name_plural = 'Приватні повідомлення'


    def clean(self):
        if not Friendship.objects.filter(
            Q(from_user=self.sender, to_user=self.receiver) | 
            Q(from_user=self.receiver, to_user=self.sender),
            status='accepted'
        ).exists():
            raise ValidationError("Приватні повідомлення можна надсилати лише друзям.")
        

        if not self.text and not self.file:
            raise ValidationError("Повідомлення не може бути порожнім.")





