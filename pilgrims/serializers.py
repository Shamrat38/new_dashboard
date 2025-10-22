from rest_framework import serializers
from django.conf import settings
from .models import Pilgrim


class PilgrimSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Pilgrim
        fields = (
            'id',
            'office',
            'camera_count',
            'rfid_count',
            'illegal_pilgrims',
            'time_stamp',
            'image',
            'image_url',
        )

    def get_image_url(self, obj):
        """Return the full image URL, respecting DEBUG mode and BASE_URL settings."""
        if not obj.image:
            return None
        if settings.DEBUG:
            return f"{settings.BASE_URL}{obj.image.url}"
        return obj.image.url