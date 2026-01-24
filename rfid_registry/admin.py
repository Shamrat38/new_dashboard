from django.contrib import admin

from django.contrib import admin
from .models import RFIDTag


@admin.register(RFIDTag)
class RFIDTagAdmin(admin.ModelAdmin):
    list_display = ("epc_code", "name", "category", "is_active")
    search_fields = ("epc_code", "name")

