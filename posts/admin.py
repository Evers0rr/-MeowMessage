from django.contrib import admin
from .models import Post, Comment, Like
# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'privacy_status', 'created_at', 'updated_at')
    search_fields = ('author__username', 'content')
    list_filter = ('privacy_status', 'created_at')
    ordering = ('-created_at',)
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at', 'updated_at')
    search_fields = ('author__username', 'content', 'post__id')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('like_type', 'user', 'post', 'created_at')
    search_fields = ('user__username', 'post__id')
    list_filter = ('like_type', 'created_at')
    ordering = ('-created_at',)
    


