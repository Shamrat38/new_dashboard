from django.db import models
from django.core.exceptions import ValidationError
from authentication.models import BaseModel, MyUser
from office.models import Office

type_choices = [
    ("guard", "guard"),
    ("kitchen", "kitchen"),
    ("garbage", "garbage"),
    ("buffet", "buffet"),
    ("bathroom", "bathroom"),
    ("sentiment", "sentiment"),
    ("peoplecount", "peoplecount")
]

class CameraType(models.Model):
    """Model to store individual camera types"""
    type = models.CharField(max_length=255, choices=type_choices, unique=True)
    name = models.CharField(
        max_length=255, default=None, null=True, blank=True)
    name_ar = models.CharField(
        max_length=255, default=None, null=True, blank=True)

    def __str__(self):
        return self.type
class Camera(BaseModel):
    sn = models.CharField(max_length=255, unique=True)
    office = models.ForeignKey(
        Office, on_delete=models.SET_NULL, null=True, blank=True, related_name="camera")
    heart_beat_time = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        max_length=255, choices=type_choices, default="guard")
    video_link = models.URLField(null=True, blank=True)

    def __str__(self):
        company_name = self.office.company.name if self.office and self.office.company else "No Company"
        office_name = self.office.name if self.office else "No Office"
        office_pk = self.office.pk if self.office else "No Office"
        return f"{company_name} - office_name:{office_name}->office_pk:{office_pk} -> {self.sn}"

    def clean(self):
        if self.sn and self.office and self.office.company:
            existing = Camera.objects.filter(
                sn=self.sn,
                tent__company=self.office.company
            )
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    f"Camera with SN '{self.sn}' already exists in this company.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
class CounterHistory(BaseModel):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    sn = models.CharField(max_length=255)
    total_in = models.IntegerField(default=0)
    total_out = models.IntegerField(default=0)
    passby = models.IntegerField(default=0)
    turnback = models.IntegerField(default=0)
    avg_stay_time = models.IntegerField(default=0)
    in_adult = models.IntegerField(default=0)
    out_adult = models.IntegerField(default=0)
    passby_adult = models.IntegerField(default=0)
    turnback_adult = models.IntegerField(default=0)
    in_child = models.IntegerField(default=0)
    out_child = models.IntegerField(default=0)
    passby_child = models.IntegerField(default=0)
    turnback_child = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(
        upload_to='counter_image/%Y/%m/%d/', default="", blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total = self.total_in - self.total_out
        super().save(*args, **kwargs)