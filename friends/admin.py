from django.contrib import admin
from .models import Friendrequest, Friendship, Subscribers
from django.utils import timezone

# Register your models here.

@admin.register(Friendrequest)
class FriendrequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'created_at', 'accepted')
    list_filter = ('accepted', 'created_at')
    search_fields = ('sender__username', 'receiver__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at')
    search_fields = ('user1__username', 'user2__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_at = timezone.now()
        super().save_model(request, obj, form, change)
@admin.register(Subscribers)
class SubscribersAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'created_at')
    search_fields = ('user__username', 'channel__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_at = timezone.now()
        super().save_model(request, obj, form, change)


