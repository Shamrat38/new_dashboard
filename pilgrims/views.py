from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from datetime import timedelta
from .models import Camera, RFID, Pilgrim
from authentication.permissions import PeopleCountPermission
from office.models import Office
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse, QueryDict
from .serializers import PilgrimSerializer

import pytz, os
from django.utils import timezone
from datetime import datetime, time

@method_decorator(csrf_exempt, name='dispatch')
class CameraCounterView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request):
        sn = request.data.get('sn')
        camera_count = request.data.get('count')
        time_stamp = request.data.get('time_stamp')
        image = request.data.get('image')

        if not all([sn, camera_count, time_stamp]):
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            camera = Camera.objects.get(sn=sn)
            office = camera.office
        except Camera.DoesNotExist:
            return Response({'error': 'Invalid Camera SN'}, status=status.HTTP_404_NOT_FOUND)

        time_obj = datetime.fromisoformat(time_stamp)

        pilgrim, created = Pilgrim.objects.get_or_create(
            office=office,
            time_stamp=time_obj,
            defaults={'camera_count': camera_count, 'image': image}
        )

        # Update existing
        if not created:
            pilgrim.camera_count = camera_count

            # ⚙️ Temporary save the image
            if image:
                pilgrim.image = image

            # ✅ Check illegal pilgrims
            if pilgrim.rfid_count is not None:
                diff = pilgrim.camera_count - pilgrim.rfid_count
                if diff > 0:
                    pilgrim.illegal_pilgrims = diff
                else:
                    pilgrim.illegal_pilgrims = 0
                    # ❌ Remove image if exists and not illegal
                    if pilgrim.image:
                        image_path = pilgrim.image.path
                        pilgrim.image.delete(save=False)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                        pilgrim.image = None

            pilgrim.save()

        serializer = PilgrimSerializer(pilgrim, context={"request": request})
        return Response(
            {"message": "Data processed successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

@method_decorator(csrf_exempt, name='dispatch')
class RFIDCounterView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request):
        sn = request.data.get('sn')
        rfid_count = request.data.get('count')
        time_stamp = request.data.get('time_stamp')

        if not all([sn, rfid_count, time_stamp]):
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rfid = RFID.objects.get(sn=sn)
            office = rfid.office
        except RFID.DoesNotExist:
            return Response({'error': 'Invalid RFID SN'}, status=status.HTTP_404_NOT_FOUND)

        time_obj = datetime.fromisoformat(time_stamp)

        pilgrim, created = Pilgrim.objects.get_or_create(
            office=office,
            time_stamp=time_obj,
            defaults={'rfid_count': rfid_count}
        )

        if not created:
            pilgrim.rfid_count = rfid_count

            # ✅ Check illegal pilgrims
            if pilgrim.camera_count is not None:
                diff = pilgrim.camera_count - pilgrim.rfid_count
                if diff > 0:
                    pilgrim.illegal_pilgrims = diff
                else:
                    pilgrim.illegal_pilgrims = 0
                    # ❌ Remove image if exists (no illegal)
                    if pilgrim.image and hasattr(pilgrim.image, 'path'):
                        image_path = pilgrim.image.path
                        pilgrim.image.delete(save=False)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                        pilgrim.image = None

            pilgrim.save()

        serializer = PilgrimSerializer(pilgrim, context={"request": request})
        return Response(
            {"message": "Data processed successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )