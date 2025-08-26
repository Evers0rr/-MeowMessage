from django.contrib import admin
from .models import Feedback, Rating
# Register your models here.

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'feedback_type', 'post', 'group', 'group_post', 'created_at')
    list_filter = ('feedback_type', 'created_at')
    search_fields = ('user__username', 'content')
    ordering = ('-created_at',)
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'group_post', 'group', 'score', 'created_at')
    list_filter = ('rating_type_choices', 'score', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)


