from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse

class Post(models.Model):
    privacy_choices = [
        ('public', 'Публічний'),
        ('friends', 'Тільки друзі'),
        # ('private', 'Приватний'), реалізую потім
    ]
    privacy_status = models.CharField(
        max_length=10,
        choices=privacy_choices,
        default='public',
        verbose_name='Статус конфіденційності'
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=80)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.title.strip():
            raise ValidationError("Назва посту не може бути порожньою.")
        if not self.content.strip() and not self.image:
            raise ValidationError("Пост повинен містити або текст, або зображення.")
        
    def __str__(self):
        return f"Пост від {self.author.username} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_absolute_url(self):
        return reverse('posts:post_detail', kwargs={'pk': self.pk})
    
    def get_likes_count(self):
        return self.likes.filter(like_type='like').count()
    
    def get_dislikes_count(self):
        return self.likes.filter(like_type='dislike').count()
    
    def get_comments_count(self):
        return self.comments.count()
    
    def can_view(self, user):
        if self.privacy_status == 'public':
            return True
        elif self.privacy_status == 'friends':
            return user.is_authenticated and (user == self.author or user in self.author.friends())
        elif self.privacy_status == 'private':
            return user == self.author
        return False
    
    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Пости'
        ordering = ['-created_at']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=500)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Коментар від {self.author.username} до посту {self.post.id} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_replies_count(self):
        return self.replies.count()
    
    class Meta:
        verbose_name = 'Коментар'
        verbose_name_plural = 'Коментарі'
        ordering = ['created_at']

class Like(models.Model):
    like_type_choices = [
        ('like', '👍'),
        ('dislike', '👎'),
    ]  
    like_type = models.CharField(
        max_length=10,
        choices=like_type_choices,
        verbose_name='Тип лайку'
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
       
    def __str__(self):
        return f"Лайк від {self.user.username} до посту {self.post.id} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_user_reaction_per_post')
        ]
        ordering = ['-created_at']

