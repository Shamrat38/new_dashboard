from django.contrib import admin
from .models import Camera

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    search_fields = ['sn', 'id']
    list_display = ['id', 'office', 'sn']