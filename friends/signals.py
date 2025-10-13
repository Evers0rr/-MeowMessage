from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Friendship, Friendrequest
from django.db.models import Q

@receiver(post_save, sender=Friendship)
def cleanup_friend_requests(sender, instance, created, **kwargs):
    if created:
        Friendrequest.objects.filter(
            (Q(sender=instance.user1, receiver=instance.user2) |
             Q(sender=instance.user2, receiver=instance.user1))
        ).delete()