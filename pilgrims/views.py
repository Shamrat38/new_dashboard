from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Camera, RFID, Pilgrim
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import PilgrimSerializer
from django.utils.dateparse import parse_datetime
from datetime import datetime

import pytz, os

saudi_tz = pytz.timezone('Asia/Riyadh')

def start_end_time_to_riyad(dt):
    if dt.tzinfo is None:
        return saudi_tz.localize(dt)
    return dt.astimezone(saudi_tz)


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
            camera_count = int(camera_count)
        except ValueError:
            return Response({'error': 'Invalid camera_count value'}, status=status.HTTP_400_BAD_REQUEST)
        
        
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
                diff = int(pilgrim.camera_count) - int(pilgrim.rfid_count)
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
            rfid_count = int(rfid_count)
        except ValueError:
            return Response({'error': 'Invalid rfid_count value'}, status=status.HTTP_400_BAD_REQUEST)
        
        
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
                diff = int(pilgrim.camera_count) - int(pilgrim.rfid_count)
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
        
        
class IlligalPilgrimsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        GET:
        - /pilgrims/illegal-pilgrims/?office=1,2,3&start_date=2025-10-20T00:00:00&end_date=2025-10-22T23:59:59
        - /pilgrims/illegal-pilgrims/<id>/
        """
        office_param = request.GET.get("office")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        pk = kwargs.get("pk", None)
        if pk:
            try:
                pilgrim = Pilgrim.objects.get(pk=pk, illegal_pilgrims__gt=0)
            except Pilgrim.DoesNotExist:
                return Response({"error": "Pilgrim not found or not illegal."}, status=404)

            serializer = PilgrimSerializer(pilgrim, context={"request": request})
            return Response(serializer.data, status=200)
        
        # ⚠️ All filters mandatory
        if not all([office_param, start_date, end_date]):
            return Response(
                {"error": "Missing required filters: office, start_date, end_date"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        # Parse multiple office IDs
        try:
            office_ids = [int(o.strip()) for o in office_param.split(",") if o.strip()]
        except ValueError:
            return Response({"error": "Invalid office parameter"}, status=400)

        # Parse dates
        start = parse_datetime(start_date)
        end = parse_datetime(end_date)
        if not (start and end):
            return Response({"error": "Invalid date format"}, status=400)
        
        start = start_end_time_to_riyad(start)
        end = start_end_time_to_riyad(end)

        # ✅ Query only illegal pilgrims within range & office list
        pilgrims = Pilgrim.objects.filter(
            illegal_pilgrims__gt=0,
            office_id__in=office_ids,
            time_stamp__range=(start, end),
        ).order_by("-time_stamp")

        serializer = PilgrimSerializer(pilgrims, many=True, context={"request": request})
        return Response(serializer.data, status=200)