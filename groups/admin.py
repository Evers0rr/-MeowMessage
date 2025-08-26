from django.contrib import admin
from .models import Group, MemberShip, GroupCategory, GroupPost, GroupComment, GroupJoinRequest, GroupInvitation

# Register your models here.
@admin.register(GroupCategory)
class GroupCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'public_or_private', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('category', 'public_or_private', 'created_at')
    ordering = ('-created_at',)
    filter_horizontal = ('members',)
@admin.register(MemberShip)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    search_fields = ('user__username', 'group__name', 'role')
    list_filter = ('role', 'joined_at')
    ordering = ('-joined_at',)
@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ('group', 'author', 'created_at')
    search_fields = ('group__name', 'author__username', 'content')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
@admin.register(GroupComment)
class GroupCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    search_fields = ('post__content', 'author__username', 'content')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
@admin.register(GroupJoinRequest)
class GroupJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'status', 'requested_at')
    search_fields = ('user__username', 'group__name', 'status')
    list_filter = ('status', 'requested_at')
    ordering = ('-requested_at',)
@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = ('inviter', 'invitee', 'group', 'status', 'invited_at')
    search_fields = ('inviter__username', 'invitee__username', 'group__name', 'status')
    list_filter = ('status', 'invited_at')
    ordering = ('-invited_at',)



