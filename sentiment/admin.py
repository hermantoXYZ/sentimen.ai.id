from django.contrib import admin
from .models import UserQuota, AnalysisLog


@admin.register(UserQuota)
class UserQuotaAdmin(admin.ModelAdmin):
    list_display = ('user', 'used_today', 'daily_limit', 'remaining', 'last_reset')
    list_editable = ('daily_limit',)
    search_fields = ('user__username',)


@admin.register(AnalysisLog)
class AnalysisLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'input_preview', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('user__username', 'input_preview')