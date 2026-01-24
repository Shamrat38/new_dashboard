from django.db import models

from django.db import models


class RFIDTag(models.Model):
    epc_code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)  # staff / pilgrim / cleaner / guard
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.epc_code})"

