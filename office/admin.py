from django.contrib import admin

from .models import Office, Country

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    search_fields = ['name', 'name_ar']
    list_display = ['id','name', 'name_ar']

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location')
    search_fields = ('name', 'location')