from django.db import models
from django.conf import settings
from posts.models import Post
from groups.models import Group, GroupPost
from django.core.exceptions import ValidationError

# Create your models here.

feedback_type_choices = [
    ('post', 'Публікація'),
    ('group', 'Група'),
    ('group_post', 'Публікація в групі'),
]

rating_type_choices = [
    ('post', 'Публікація'),
    ('group', 'Група'),
    ('group_post', 'Публікація в групі'),
]

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_type = models.CharField(max_length=20, choices=feedback_type_choices)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='feedbacks', blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='feedbacks', blank=True, null=True)
    group_post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='feedbacks', blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.feedback_type == 'post' and not self.post:
            raise ValidationError("Публікація повинна бути вказана для типу 'post'.")
        if self.feedback_type == 'group' and not self.group:
            raise ValidationError("Група повинна бути вказана для типу 'group'.")
        if self.feedback_type == 'group_post' and not self.group_post:
            raise ValidationError("Публікація в групі повинна бути вказана для типу 'group_post'.")
        if self.feedback_type not in dict(feedback_type_choices).keys():
            raise ValidationError("Недійсний тип відгуку.")
        if not self.content.strip():
            raise ValidationError("Відгук не може бути порожнім.")

        filters = {'user': self.user, 'feedback_type': self.feedback_type}

        if self.feedback_type == 'post' and self.post:
            filters['post_id'] = self.post.id
        elif self.feedback_type == 'group' and self.group:
            filters['group_id'] = self.group.id
        elif self.feedback_type == 'group_post' and self.group_post:
            filters['group_post_id'] = self.group_post.id

        existing_feedback = Feedback.objects.filter(**filters)

        if self.pk:
            existing_feedback = existing_feedback.exclude(pk=self.pk)

        if existing_feedback.exists():
            raise ValidationError("Ви вже залишили відгук на цей об'єкт.")

    def __str__(self):
        return f"Відгук від {self.user} на {self.post or self.group or self.group_post}"
    
    class Meta:
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'
        ordering = ['-created_at']

class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    rating_type_choices = models.CharField(max_length=20, choices=rating_type_choices)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='ratings', blank=True, null=True)
    group_post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='ratings', blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='ratings', blank=True, null=True)
    score = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.post and not self.group_post and not self.group:
            raise ValidationError("Оцінка повинна бути для публікації, публікації в групі або групи.")
        if self.group and (self.post or self.group_post):
            raise ValidationError("Оцінка для групи не може бути пов'язана з публікацією.")
        if self.score < 1 or self.score > 10:
            raise ValidationError("Оцінка повинна бути в межах від 1 до 10.")
        if self.post and self.group:
            raise ValidationError("Оцінка для публікації не може бути пов'язана з групою.")
        if self.group_post and not self.group_post.group:
            raise ValidationError("Публікація в групі повинна належати до групи.")

    def __str__(self):
        return f"Оцінка від {self.user} на {self.post or self.group_post or self.group} | Оцінка: {self.score}"
    
    class Meta:
        verbose_name = 'Оцінка'
        verbose_name_plural = 'Оцінки'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_post_rating'),
            models.UniqueConstraint(fields=['user', 'group_post'], name='unique_user_group_post_rating'),
            models.UniqueConstraint(fields=['user', 'group'], name='unique_user_group_rating')
        ]


