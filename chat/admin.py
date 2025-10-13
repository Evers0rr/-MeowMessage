from django.contrib import admin
from .models import GroupChat, GroupMessage, PrivateMessage

# Register your models here.

@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content_type', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'text')
    list_filter = ('content_type', 'created_at')
    ordering = ('-created_at',)

@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_members_count', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)

    def get_members_count(self, obj):
        return obj.members.count()
    get_members_count.short_description = 'Кількість учасників'

@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'sender', 'content_type', 'created_at')
    search_fields = ('chat__name', 'sender__username', 'text')
    list_filter = ('content_type', 'created_at')
    ordering = ('-created_at',)


