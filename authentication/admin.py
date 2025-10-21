from django.contrib import admin


from .models import MyUser, Company
from .forms import MyUserCreationForm


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    

@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    add_form = MyUserCreationForm
    list_display = ('email', 'username', 'is_admin', 'company')
    search_fields = ('email', 'username')
    readonly_fields = ('date_joined', 'last_login')

    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'company',
                'password1',
                'password2',
                'is_admin',
                'is_active',
                'is_staff',
                'is_superuser',
                'is_annotator',
                'company_annotator',
                'camera_type_annotator',
                'sensor_update_permission',
                'assigned_office',
                # Add PermissionModel fields
                'is_temperature',
                'is_guard',
                'is_peoplecount',
                'is_kitchen',
                'is_foodweight',
                'is_cleanness',
                'is_buffet',
                'is_cleaners',
                'is_sentiment',
                'is_water_tank',
                'is_sensor_assign',
                'is_annotator_ranking'
            ),
        }),
    )

    # Fields for editing an existing user
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'company')
        }),
        ('Permissions', {
            'fields': (
                'is_admin',
                'is_active',
                'is_staff',
                'is_superuser',
                'is_annotator',
                'sensor_update_permission',
                # Add PermissionModel fields
                'is_temperature',
                'is_guard',
                'is_peoplecount',
                'is_kitchen',
                'is_foodweight',
                'is_cleanness',
                'is_buffet',
                'is_cleaners',
                'is_sentiment',
                'is_water_tank',
                'is_sensor_assign',
                'is_annotator_ranking'
            )
        }),
        ('Associations', {
            'fields': ('company_annotator', 'camera_type_annotator', 'assigned_office')
        }),
        ('Important dates', {
            'fields': ('date_joined', 'last_login')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:  # If creating a new user
            return self.add_fieldsets
        return self.fieldsets  # If editing an existing user

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)