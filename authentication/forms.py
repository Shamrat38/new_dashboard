# authentication/forms.py
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from authentication.models import MyUser, Company


class MyUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = (
            'email',
            'username',
            'company',
            'is_admin',
            'is_active',
            'is_staff',
            'is_superuser',
            'is_annotator',
            'company_annotator',
            'sensor_update_permission',
            'assigned_office'
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # Handle ManyToManyField relationships after saving the user
            if self.cleaned_data.get('company_annotator'):
                user.company_annotator.set(
                    self.cleaned_data['company_annotator'])
            if self.cleaned_data.get('assigned_office'):
                user.assigned_office.set(self.cleaned_data['assigned_office'])
        return user