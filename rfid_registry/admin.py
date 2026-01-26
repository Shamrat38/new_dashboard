from django.contrib import admin
from .models import RFIDTag
from django.utils.html import format_html

@admin.register(RFIDTag)
class RFIDTagAdmin(admin.ModelAdmin):
    list_display = ("epc_code", "name", "category", "office", "is_active", "image_preview")
    search_fields = ("epc_code", "name")
    list_filter = ("category", "office", "is_active")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image.url)
        return "No Image"

    image_preview.short_description = "Image"
