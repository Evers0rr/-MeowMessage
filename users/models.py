from django.db import models
from django.contrib.auth.models import AbstractUser
from friends.models import Friendship, Subscribers

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
    new_email = models.EmailField(blank=True, null=True)
    new_email_at = models.DateTimeField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/',default='avatars/default.jpg', blank=True, null=True)
    status = models.CharField(max_length=23, blank=True)
    subscribers = models.ManyToManyField('self', through=Subscribers, symmetrical=False, blank=True, related_name='subscribers_to')

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
    
    def country_name(self):
        if self.country:
            return self.country.name
        return "Не вказано"
    
    def get_subscribers_count(self):
        return Subscribers.objects.filter(channel=self).count()
    
    def get_subscriptions_count(self):
        return Subscribers.objects.filter(user=self).count()
    
    def get_subscribers(self):
        return User.objects.filter(
            id__in=Subscribers.objects.filter(channel=self).values('user')
        )
    
    def get_subscriptions(self):
        return User.objects.filter(
            id__in=Subscribers.objects.filter(user=self).values('channel')
        )
        
    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
        ordering = ['username']



