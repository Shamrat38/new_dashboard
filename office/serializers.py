from rest_framework import serializers
from .models import Office
class OfficeSerializer(serializers.ModelSerializer):
    map_image_url = serializers.SerializerMethodField()
    office_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Office
        fields = (
            "id",
            "name",
            "longitude",
            "latitude",
            "location",
            "map_image",
            "map_image_url",
            "office_image",
            "office_image_url",
            "created_by",
            "nationality",
        )
        read_only_fields = ("id", "created_by")

    def get_map_image_url(self, obj):
        request = self.context.get('request')
        if obj.map_image and hasattr(obj.map_image, 'url'):
            return request.build_absolute_uri(obj.map_image.url)
        return None

    def get_office_image_url(self, obj):
        request = self.context.get('request')
        if obj.office_image and hasattr(obj.office_image, 'url'):
            return request.build_absolute_uri(obj.office_image.url)
        return None


    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        validated_data["company"] = request.user.company
        return super().create(validated_data)
