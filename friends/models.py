from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
# Create your models here.

class Friendrequest(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_requests',
        on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_requests',
        on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def clean(self):
        if self.sender == self.receiver:
            raise ValidationError("Ти не можеш відправити запит на дружбу самому собі.")

    def __str__(self):
        status = "✅ Прийнято" if self.accepted else "⏳ Очікує на підтвердження"
        return f"{self.sender} → {self.receiver} ({status})"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['sender', 'receiver'],
                name='unique_friend_request'
            )
        ]
        verbose_name = 'Запит на дружбу'
        verbose_name_plural = 'Запити на дружбу'
        ordering = ['-created_at']

class Friendship(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendships_as_user1',
        on_delete=models.CASCADE)
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendships_as_user2',
        on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user1} & {self.user2} (Дружба з {self.created_at.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user1', 'user2'],
                name='unique_friendship'
            )
        ]

    
    
    
    




