from django.db import models
from django.core.exceptions import ValidationError
from authentication.models import BaseModel, MyUser
from office.models import Office


class RFID(BaseModel):
    sn = models.CharField(max_length=255, unique=True)
    office = models.OneToOneField(Office, on_delete=models.SET_NULL, null=True, blank=True, related_name="rfid")
    heart_beat_time = models.DateTimeField(auto_now_add=True)
    video_link = models.URLField(null=True, blank=True)

    def __str__(self):
        company_name = self.office.company.name if self.office and self.office.company else "No Company"
        office_name = self.office.name if self.office else "No Office"
        office_pk = self.office.pk if self.office else "No Office"
        return f"{company_name} - office_name:{office_name}->office_pk:{office_pk} -> {self.sn}"

    def clean(self):
        if self.sn and self.office and self.office.company:
            existing = RFID.objects.filter(
                sn=self.sn,
                office__company=self.office.company
            )
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    f"Camera with SN '{self.sn}' already exists in this company.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Camera(BaseModel):
    sn = models.CharField(max_length=255, unique=True)
    office = models.OneToOneField(Office, on_delete=models.SET_NULL, null=True, blank=True, related_name="camera")
    heart_beat_time = models.DateTimeField(auto_now_add=True)
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
                office__company=self.office.company
            )
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    f"Camera with SN '{self.sn}' already exists in this company.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Pilgrim(BaseModel):
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    camera_count = models.IntegerField(null=True, blank=True)
    rfid_count = models.IntegerField(null=True, blank=True)
    time_stamp = models.DateTimeField()
    image = models.ImageField(upload_to='counter_image/%Y/%m/%d/', default="", blank=True, null=True)
    illegal_pilgrims = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.office} - {self.time_stamp}"
    


"""class CameraCounter(BaseModel):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    sn = models.CharField(max_length=255)
    count = models.IntegerField(default=0)
    time_stamp = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='counter_image/%Y/%m/%d/', default="", blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
class RFIDCounter(BaseModel):
    rfid = models.ForeignKey(RFID, on_delete=models.CASCADE)
    sn = models.CharField(max_length=255)
    count = models.IntegerField(default=0)
    time_stamp = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)"""