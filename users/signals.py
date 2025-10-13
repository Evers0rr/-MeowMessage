import os
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def delete_old_avatar(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_avatar = sender.objects.get(pk=instance.pk).avatar
    except sender.DoesNotExist:
        return

    new_avatar = instance.avatar
    if old_avatar and old_avatar != new_avatar and old_avatar.name != "avatars/default.jpg":
        old_path = os.path.join(settings.MEDIA_ROOT, old_avatar.name)
        if os.path.isfile(old_path):
            os.remove(old_path)