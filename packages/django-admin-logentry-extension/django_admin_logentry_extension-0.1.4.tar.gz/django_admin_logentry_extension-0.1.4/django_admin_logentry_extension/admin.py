from django.contrib import admin
from django_admin_daterange_listfilter.filters import DateRangeFilter
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model

User = get_user_model()


class LogEntryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "action_flag",
        "content_type",
        "object_repr",
        "object_id",
        "action_time",
    ]
    list_filter = [
        "user",
        "content_type",
        "action_flag",
        ("action_time", DateRangeFilter),
    ]
    ordering = [
        "-pk",
    ]
    list_per_page = 10

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


admin.site.register(LogEntry, LogEntryAdmin)
