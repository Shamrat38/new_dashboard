from rest_framework import serializers
from django.conf import settings
from camera.models import CounterHistory


class CounterHistorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CounterHistory
        fields = ('camera', 'sn', 'total_in', 'total_out', 'passby', 'turnback', 'avg_stay_time', 'in_adult', 'out_adult', 'passby_adult',
                  'turnback_adult', 'in_child', 'out_child', 'passby_child', 'turnback_child', 'total', 'start_time', 'end_time', 'created_at', 'updated_at', 'image', 'image_url')

    def get_image_url(self, obj):
        # Check if the image exists and if DEBUG is True
        if obj.image and settings.DEBUG:
            return f"{settings.BASE_URL}{obj.image.url}"
        # Return the default URL if not in DEBUG mode or image doesn't exist
        return obj.image.url if obj.image else None