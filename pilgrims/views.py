from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Camera, RFID, CameraCounter, RFIDCounter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import PilgrimSerializer
from django.utils.dateparse import parse_datetime
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse
from django.db.models import Sum
import pytz, os

saudi_tz = pytz.timezone('Asia/Riyadh')

def start_end_time_to_riyad(dt):
    if dt.tzinfo is None:
        return saudi_tz.localize(dt)
    return dt.astimezone(saudi_tz)

def normalize_time(ts):
    obj = datetime.fromisoformat(ts)
    return obj.replace(microsecond=0)


@method_decorator(csrf_exempt, name='dispatch')
class CameraCounterView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        sn = request.data.get("sn")
        camera_count = request.data.get("camera_count")
        time_stamp = request.data.get("time_stamp")
        image = request.data.get("image")

        if not all([sn, camera_count, time_stamp]):
            return Response({"error": "Missing fields"}, status=400)

        try:
            camera = Camera.objects.get(sn=sn)
            office = camera.office
        except Camera.DoesNotExist:
            return Response({"error": "Invalid Camera SN"}, status=404)

        obj = CameraCounter.objects.create(
            office=office,
            sn=sn,
            camera_count=int(camera_count),
            time_stamp=datetime.fromisoformat(time_stamp),
            image=image,
        )

        return Response({
            "message": "Camera data stored",
            "id": obj.id
        }, status=201)
        
@method_decorator(csrf_exempt, name='dispatch')
class RFIDCounterView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        sn = request.data.get("sn")
        rfid_count = request.data.get("rfid_count")
        time_stamp = request.data.get("time_stamp")

        if not all([sn, rfid_count, time_stamp]):
            return Response({"error": "Missing fields"}, status=400)

        try:
            rfid = RFID.objects.get(sn=sn)
            office = rfid.office
        except RFID.DoesNotExist:
            return Response({"error": "Invalid RFID SN"}, status=404)

        obj = RFIDCounter.objects.create(
            office=office,
            sn=sn,
            rfid_count=int(rfid_count),
            time_stamp=datetime.fromisoformat(time_stamp),
        )

        return Response({
            "message": "RFID data stored",
            "id": obj.id
        }, status=201)

"""@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pilgrims_statistics_for_tent(request, tent_id, date=None):
    
    camera_stats = []
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=400)

        # Calculate the start and end of the day for filtering
        start_time = filter_date.replace(
            hour=0, minute=0, second=0, microsecond=0)
        end_time = filter_date.replace(
            hour=23, minute=59, second=59, microsecond=999999)
        counter_history = Pilgrim.objects.filter(
            office=tent_id, time_stamp__range=[start_time, end_time])

        # Sum the total_in and total_out for the specific date range
        total_camera_count = counter_history.aggregate(Sum('camera_count'))[
            'camera_count__sum'] or 0
        total_rfid_count = counter_history.aggregate(Sum('rfid_count'))[
            'rfid_count__sum'] or 0
        
        total_pilgrims_count = counter_history.aggregate(Sum('illegal_pilgrims'))[
            'illegal_pilgrims__sum'] or 0

        # Append the summed values for the cameras on the specific date
        camera_stats.append({
            'tent_id': tent_id,
            'total_camera_count': total_camera_count,
            'total_rfid_count': total_rfid_count,
            'total_illegal_pilgrims': total_pilgrims_count,
            'date': date
        })
    else:
        # If no date is provided, calculate the sums for all available data
        pilgrims_data = Pilgrim.objects.filter(office=tent_id)
        total_camera_count = pilgrims_data.aggregate(Sum('camera_count'))[
            'camera_count__sum'] or 0
        total_rfid_count = pilgrims_data.aggregate(Sum('rfid_count'))[
            'rfid_count__sum'] or 0
        
        total_pilgrims_count = pilgrims_data.aggregate(Sum('illegal_pilgrims'))[
            'illegal_pilgrims__sum'] or 0

        camera = Camera.objects.filter(office_id=tent_id).first()
        rfid = RFID.objects.filter(office_id=tent_id).first()

        camera_stats.append({
            'camera_sn': camera.sn if camera else None,
            'rfid_sn': rfid.sn  if rfid else None,
            'total_camera_count': total_camera_count,
            'total_rfid_count': total_rfid_count,
            'total_illegal_pilgrims': total_pilgrims_count,
            #'heartbeat_time': heartbeat_time
        })

    # Return the result as JSON
    data = {
        "success": True,
        "message": "Camera statistics Fetched Successfully",
        "camera_statistics": camera_stats
    }
    return Response(data, status=status.HTTP_200_OK)


        
        
class IlligalPilgrimsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        #GET:
        #- /pilgrims/illegal-pilgrims/?office=1,2,3&start_date=2025-10-20T00:00:00&end_date=2025-10-22T23:59:59
        #- /pilgrims/illegal-pilgrims/<id>/
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
    
    
class PilgrimFramesAPIView(APIView):
    
    #Returns illegal pilgrim frames based only on tent (office) id.
    #URL: /pilgrims/pilgrim-frames/?tent_ids=1&page=1&page_size=30
    

    def get(self, request):
        tent_ids = request.GET.get("tent_ids", None)
        page = request.GET.get("page", 1)
        page_size = request.GET.get("page_size", 30)

        if not tent_ids:
            return Response({"message": "tent_ids parameter is required"}, status=400)

        queryset = Pilgrim.objects.filter(
            office__id=tent_ids,
            illegal_pilgrims__gt=0,  # ✅ Only illegal frames
            image__isnull=False      # ✅ Must have image
        ).order_by("-time_stamp")     # newest first

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(queryset, request)

        data = [
            {
                "id": pilgrim.id,
                "time": pilgrim.time_stamp,
                "illegal_pilgrims": pilgrim.illegal_pilgrims,
                "image": request.build_absolute_uri(pilgrim.image.url) if pilgrim.image else None,
                "current_status": ["illegal"],      # ✅ frontend expects array
            }
            for pilgrim in result_page
        ]

        return paginator.get_paginated_response(data)
"""