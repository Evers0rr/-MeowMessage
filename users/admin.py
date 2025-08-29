from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'privacy_status', 'is_staff', 'is_active', 'get_subscribers_count'
    )

    def get_subscribers_count(self, obj):
        return obj.subscribers_to.count()
    get_subscribers_count.short_description = 'Підписники'

    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('privacy_status', 'is_staff', 'is_active')
    ordering = ('username',)

