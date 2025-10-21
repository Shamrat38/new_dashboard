from django.db import models
from authentication.models import BaseModel, Company

class Country(BaseModel):
    name = models.CharField(max_length=255, null=False, blank=False)
    name_ar = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name
    class Meta:
        ordering = ['id']

class Office(BaseModel):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, null=True, blank=False, related_name="office")
    name = models.CharField(max_length=255, null=False, blank=False)
    longitude = models.CharField(max_length=255, null=False, blank=False)
    latitude = models.CharField(max_length=255, null=False, blank=False)
    location = models.TextField(null=True, blank=True)
    map_image = models.ImageField(upload_to='images/%Y/%m/%d/', blank=True, null=True)
    created_by = models.ForeignKey("authentication.MyUser", on_delete=models.SET_NULL, null=True, blank=True)
    office_image = models.ImageField(upload_to='images_office/%Y/%m/%d/', blank=True, null=True)

    nationality = models.ManyToManyField(Country, blank=True)

    def __str__(self):
        company_name = self.company.name if self.company else "No Company"
        #arafa = "Arafa" if self.is_arafa else "Mina"
        return f"Office Pk: {self.pk} -> Office Name: {self.name} -> Company: {company_name}"


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'], name='unique_company_office_name')
        ]


