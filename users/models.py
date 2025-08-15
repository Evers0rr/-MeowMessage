from django.db import models
from django.contrib.auth.models import AbstractUser
from friends.models import Friendship

# Create your models here.

class User(AbstractUser):
    PRIVACY_CHOICES = [
        ('public', 'Публічний'),
        ('friends', 'Тільки друзі'),
        ('private', 'Приватний'),
    ]

    privacy_status = models.CharField(
        max_length=10,
        choices=PRIVACY_CHOICES,
        default='public',
        verbose_name='Статус конфіденційності'
    )
    bio = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cover_image = models.ImageField(
        upload_to='covers/',
        blank=True,
        null=True)

    def __str__(self):
        return self.username
    
    def friends(self):
        friendships = Friendship.objects.filter(
            models.Q(user1=self) | models.Q(user2=self)
        )
        return [fs.user2 if fs.user1 == self else fs.user1 for fs in friendships]

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
        ordering = ['username']



