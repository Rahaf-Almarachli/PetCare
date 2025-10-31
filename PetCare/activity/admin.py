from django.contrib import admin
from .models import Activity, ActivityLog

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'system_name', 'points_value', 'interaction_type')
    search_fields = ('name', 'system_name')
    list_filter = ('interaction_type',)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'points_awarded', 'created_at')
    list_filter = ('activity',)
    search_fields = ('user__email', 'activity__name', 'description')
    readonly_fields = ('user', 'activity', 'points_awarded', 'created_at', 'description')