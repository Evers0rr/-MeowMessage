from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import User

@shared_task
def delete_inactive_users():
    expiration_time = timezone.now() - timedelta(minutes=10)
    users = User.objects.filter(is_active=False, date_joined__lt=expiration_time)
    count = users.count()
    users.delete()
    return f"Видалено {count} неактивних користувачів"


@shared_task
def reset_new_email():
    threshold = timezone.now() - timedelta(minutes=10)
    count = User.objects.filter(
        new_email__isnull=False,
        new_email_at__lt=threshold
    ).update(new_email=None, new_email_at=None)
    return f'Скинуто {count} нових email'