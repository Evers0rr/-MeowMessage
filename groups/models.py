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
    GROUP_PUBLIC_OR_PRIVATE = [
    ('public', 'Публічна'),
    ('private', 'Приватна'),
]
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(blank=True, max_length=255)
    category = models.ForeignKey(GroupCategory, on_delete=models.CASCADE, related_name='groups', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    avatar = models.ImageField(upload_to='group_avatars/',default='group_avatars/default_group.png', blank=True, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='members', blank=True)
    public_or_private = models.CharField(max_length=10, choices=GROUP_PUBLIC_OR_PRIVATE, default='public')

    
    def clean(self):
        if self.name.strip() == "":
            raise ValidationError("Назва групи не може бути порожньою.")
        if not self.category:
            raise ValidationError("Будь ласка, виберіть категорію для групи.")
        if self.avatar and not self.avatar.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            raise ValidationError("Непідтримуваний формат зображення. Використовуйте .png, .jpg, .jpeg, .webp або .gif.")

    class Meta:
        verbose_name = 'Група'
        verbose_name_plural = 'Групи'
        ordering = ['-created_at']

    def save(self, *args, owner=None, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and owner:
            Membership = apps.get_model("groups", "Membership")
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

    def clean(self):
        if self.user not in self.group.members.all():
            raise ValidationError("Користувач повинен бути учасником групи, щоб мати членство.")
  
class GroupPost(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name='group_posts')
    title = models.CharField(max_length=80)
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
        if not self.group:
            return
       
        if not self.title.strip():
            raise ValidationError("Назва посту не може бути порожньою.")
        if not self.content.strip() and not self.image:
            raise ValidationError("Контент посту не може бути порожнім.")
        if self.image and not self.image.name.endswith(('.png', '.jpg', '.jpeg', '.gif', 'webp')):
            raise ValidationError("Непідтримуваний формат зображення. Використовуйте .png, .jpg, .jpeg, .webp або .gif.")
        if self.author not in self.group.members.all():
            raise ValidationError("Автор посту повинен бути учасником групи.")
        
    def get_comments_count(self):
        return self.comments.count()
    
    def get_likes_count(self):
        return self.group_likes.filter(like_type='like').count()
    
    def get_dislikes_count(self):
        return self.group_likes.filter(like_type='dislike').count()
        
class GroupComment(models.Model):
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
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
            raise ValidationError("Контент коментаря не може перевищувати 500 символів.")
        
        if self.post_id and self.parent and self.parent.post_id != self.post_id:
            raise ValidationError("Parent-коментар повинен належати тому ж посту.")

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
        if self.group.members.filter(id=self.user.id).exists():
            raise ValidationError("Ви вже є учасником цієї групи.")

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

        Membership = apps.get_model("groups", "MemberShip")
        membership, created = Membership.objects.get_or_create(
            user=self.invitee,
            group=self.group,
            defaults={"role": "member"}
        )
        if not created:
            membership.role = "member"
            membership.save()

        self.status = 'accepted'
        self.save()

    def decline_invitation(self):
        if self.status != 'pending':
            raise ValidationError("Запрошення вже неактивне.")
        
class GroupLike(models.Model):
    like_type_choices = [
        ('like', '👍'),
        ('dislike', '👎'),
    ]  
    like_type = models.CharField(
        max_length=10,
        choices=like_type_choices,
        verbose_name='Тип лайку'
    )
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='group_likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
       
    def __str__(self):
        return f"Лайк від {self.user.username} до групового посту {self.post.id} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_user_group_reaction_per_post')
        ]
        ordering = ['-created_at']
    