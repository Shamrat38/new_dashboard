from django.contrib import admin
from .models import Camera
from .models import RFID

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    search_fields = ['sn', 'id']
    list_display = ['id', 'office', 'sn']
    

@admin.register(RFID)
class RFIDAdmin(admin.ModelAdmin):
    search_fields = ['sn', 'id']
    list_display = ['id', 'office', 'sn']