from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.apps import apps
from django.utils import timezone
from datetime import timedelta


# Create your models here.

ROLE_CHOICES = [
    ('member', 'Учасник'),
    ('moderator', 'Модератор'),
    ('admin', 'Адміністратор'),
    ('owner', 'Власник'),
]

STATUS_CHOICES = [
    ("pending", "Очікує"),
    ("accepted", "Прийнято"),
    ("declined", "Відхилено"),
]

GROUP_PUBLIC_OR_PRIVATE = [
    ('public', 'Публічна'),
    ('private', 'Приватна'),
]


class GroupCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(blank=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = 'Категорія групи'
        verbose_name_plural = 'Категорії груп'
        ordering = ['name']

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(blank=True, max_length=255)
    category = models.ForeignKey(GroupCategory, on_delete=models.CASCADE, related_name='groups', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    avatar = models.ImageField(upload_to='group_avatars/', blank=True, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='members', blank=True)
    public_or_private = models.CharField(max_length=10, choices=GROUP_PUBLIC_OR_PRIVATE, default='public')

    
    def clean(self):
        if self.name.strip() == "":
            raise ValidationError("Назва групи не може бути порожньою.")
        if not self.description.strip():
            raise ValidationError("Опис групи не може бути порожнім.")
        if self.avatar and not self.avatar.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise ValidationError("Непідтримуваний формат зображення. Використовуйте .png, .jpg, .jpeg або .gif.")

    class Meta:
        verbose_name = 'Група'
        verbose_name_plural = 'Групи'
        ordering = ['-created_at']

    def save(self, *args, owner=None, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and owner:
            Membership = apps.get_model("your_app_name", "Membership")
            Membership.objects.create(group=self, user=owner, role="owner")
        

    def __str__(self):
        owner = self.memberships.filter(role="owner").first()
        owner_name = owner.user.username if owner else "Невідомо"
        return f'Назва групи: {self.name} | Власник: {owner_name} | Кількість учасників: {self.members.count()}'

        
class MemberShip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role})"
    
    class Meta:
        verbose_name = 'Членство'
        verbose_name_plural = 'Членства'
        ordering = ['-joined_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'group'], name='unique_membership')
        ]
         
class GroupPost(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name='group_posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='group_posts/', blank=True, null=True)

    def __str__(self):
        return f"Пост від {self.author.username} в групі {self.group.name} | Дата створення: {self.created_at}"
    
    class Meta:
        verbose_name = 'Пост групи'
        verbose_name_plural = 'Пости групи'
        ordering = ['-created_at']

    def clean(self):
        if not self.content.strip() and not self.image:
            raise ValidationError("Контент посту не може бути порожнім.")
        if self.image and not self.image.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise ValidationError("Непідтримуваний формат зображення. Використовуйте .png, .jpg, .jpeg або .gif.")

class GroupComment(models.Model):
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_comments')
    content = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Коментар від {self.author.username} до посту {self.post.id} в групі {self.post.group.name} | Дата створення: {self.created_at}"
    
    class Meta:
        verbose_name = 'Коментар групи'
        verbose_name_plural = 'Коментарі групи'
        ordering = ['-created_at']

    def clean(self):
        if not self.content.strip():
            raise ValidationError("Контент коментаря не може бути порожнім.")
        if len(self.content) > 500:
            raise ValidationError("Контент коментаря не може перевищувати 255 символів.")

class GroupJoinRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='join_requests')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Запит на приєднання від {self.user.username} до групи {self.group.name} | Статус: {self.status} | Дата запиту: {self.requested_at}"
    
    class Meta:
        verbose_name = 'Запит на приєднання до групи'
        verbose_name_plural = 'Запити на приєднання до групи'
        ordering = ['-requested_at']

    def clean(self):
        if self.status not in dict(STATUS_CHOICES):
            raise ValidationError("Невірний статус запиту на приєднання.")

class GroupInvitation(models.Model):
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_invitations')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invitations')
    invited_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Запрошення від {self.inviter.username} до {self.invitee.username} в групу {self.group.name} | Статус: {self.status} | Дата запрошення: {self.invited_at}"

    class Meta:
        verbose_name = 'Запрошення до групи'
        verbose_name_plural = 'Запрошення до групи'
        ordering = ['-invited_at']

    def clean(self):
        if self.status not in dict(STATUS_CHOICES):
            raise ValidationError("Невірний статус запрошення.")
        if self.inviter == self.invitee:
            raise ValidationError("Ви не можете запросити себе до групи.")   
                
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)

        #|----------------------------------------------------------|

        if self.group.join_requests.filter(user=self.invitee, status='pending').exists():
            raise ValidationError("Цей користувач вже має запит на приєднання до групи.")
        if self.group.members.filter(id=self.invitee.id).exists():
            raise ValidationError("Цей користувач вже є учасником групи.")
        super().save(*args, **kwargs)


    def is_valid(self):
        return self.status == 'pending' and (self.expires_at is None or timezone.now() < self.expires_at)

    def accept_invitation(self):
        if self.status != 'pending':
            raise ValidationError("Запрошення вже неактивне.")
        self.group.members.add(self.invitee)
        self.status = 'accepted'
        self.save()

    def decline_invitation(self):
        if self.status != 'pending':
            raise ValidationError("Запрошення вже неактивне.")
        
            
        

        



        
    



