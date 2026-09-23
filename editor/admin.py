from django.contrib import admin

from editor.models import EditorChangeLog, EditorInvite


@admin.register(EditorChangeLog)
class EditorChangeLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "tab", "summary")
    list_filter = ("action", "tab")
    search_fields = ("summary", "object_label", "user__username")
    readonly_fields = (
        "user",
        "created_at",
        "object_type",
        "object_id",
        "object_label",
        "tab",
        "action",
        "summary",
        "payload",
    )


@admin.register(EditorInvite)
class EditorInviteAdmin(admin.ModelAdmin):
    list_display = ("code", "note", "created_by", "created_at", "expires_at", "used_at", "revoked")
    list_filter = ("revoked",)
    search_fields = ("code", "note")
    readonly_fields = ("code", "created_at", "used_at", "used_by")
