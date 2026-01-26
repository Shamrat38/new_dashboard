from django.contrib import admin

from django.contrib import admin
from .models import RFIDTag


class RFIDTagAdmin(admin.ModelAdmin):
    list_display = ("epc_code", "name", "category", "office", "is_active")
    search_fields = ("epc_code", "name")
    list_filter = ("category", "office", "is_active")