from django.db import models
from office.models import Office 


class RFIDTag(models.Model):
    epc_code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # ✅ NEW
    office = models.ForeignKey(
        Office,
        on_delete=models.CASCADE,
        related_name="rfid_tags",
        null=True,
        blank=True
    )

    # ✅ NEW
    image = models.ImageField(
        upload_to="rfid_tags/%Y/%m/%d/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.epc_code})"

