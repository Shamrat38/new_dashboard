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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse
from django.db.models import Sum
from django.db import transaction, IntegrityError
import pytz, os

saudi_tz = pytz.timezone('Asia/Riyadh')

def start_end_time_to_riyad(dt):
    if dt.tzinfo is None:
        return saudi_tz.localize(dt)
    return dt.astimezone(saudi_tz)

def normalize_time(ts):
    obj = datetime.fromisoformat(ts)
    return obj.replace(microsecond=0)


def safe_get_or_create(office, time_obj, defaults):
    try:
        with transaction.atomic():
            pilgrim, created = Pilgrim.objects.get_or_create(
                office=office,
                time_stamp=time_obj,
                defaults=defaults
            )
            return pilgrim, created
    except IntegrityError:
        # Another request created it at the same millisecond
        pilgrim = Pilgrim.objects.get(office=office, time_stamp=time_obj)
        return pilgrim, False


@method_decorator(csrf_exempt, name='dispatch')
class CameraCounterView(APIView):

    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):

        # COMMON FIELDS
        time_stamp = request.data.get("time_stamp")
        if not time_stamp:
            return Response({"error": "Missing time_stamp"}, status=400)

        time_obj = normalize_time(time_stamp)

        camera_sn = request.data.get("camera_sn")
        camera_count = request.data.get("camera_count")
        rfid_sn = request.data.get("sn") or request.data.get("rfid_sn")
        rfid_count = request.data.get("rfid_count") or request.data.get("count")
        image = request.data.get("image")

        office = None

        # --- CAMERA PART ---
        if camera_sn:
            try:
                camera = Camera.objects.get(sn=camera_sn)
                office = camera.office
            except Camera.DoesNotExist:
                return Response({"error": "Invalid Camera SN"}, status=404)

        # --- RFID PART ---
        if rfid_sn:
            if rfid_sn == "0" or rfid_sn == "":
                return Response({"error": "Invalid RFID SN"}, status=400)

            try:
                rfid = RFID.objects.get(sn=rfid_sn)
                office = rfid.office
            except RFID.DoesNotExist:
                return Response({"error": "Invalid RFID SN"}, status=404)

        if office is None:
            return Response({"error": "No valid SN provided"}, status=400)

        # DEFAULTS on create
        defaults = {}
        if camera_count is not None:
            defaults["camera_count"] = int(camera_count)
        if rfid_count is not None:
            defaults["rfid_count"] = int(rfid_count)
        if image:
            defaults["image"] = image

        # --- SAFE UPSERT ---
        pilgrim, created = safe_get_or_create(office, time_obj, defaults)

        # --- UPDATE EXISTING ---
        if not created:

            if camera_count is not None:
                pilgrim.camera_count = int(camera_count)

            if rfid_count is not None:
                pilgrim.rfid_count = int(rfid_count)

            if image:
                pilgrim.image = image

        # --- ILLEGAL PILGRIMS ---
        if pilgrim.camera_count is not None and pilgrim.rfid_count is not None:
            diff = pilgrim.camera_count - pilgrim.rfid_count
            pilgrim.illegal_pilgrims = diff if diff > 0 else 0

            if pilgrim.illegal_pilgrims == 0 and pilgrim.image:
                if hasattr(pilgrim.image, "path") and os.path.exists(pilgrim.image.path):
                    os.remove(pilgrim.image.path)
                pilgrim.image = None

        pilgrim.save()

        return Response({
            "message": "Data processed successfully.",
            "data": PilgrimSerializer(pilgrim, context={"request": request}).data
        }, status=201)

@api_view(["GET"])
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


"""
@method_decorator(csrf_exempt, name='dispatch')
class RFIDCounterView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        sn = request.data.get('sn')
        rfid_count = request.data.get('count')
        time_stamp = request.data.get('time_stamp')

        # SN required
        if not sn or sn == "0":
            return Response({'error': 'Invalid or missing RFID SN'}, status=status.HTTP_400_BAD_REQUEST)

        if time_stamp is None:
            return Response({'error': 'Missing time_stamp'}, status=status.HTTP_400_BAD_REQUEST)

        if rfid_count is None:
            return Response({'error': 'Missing count'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rfid_count = int(rfid_count)
        except ValueError:
            return Response({'error': 'Invalid rfid_count value'}, status=status.HTTP_400_BAD_REQUEST)

        # RFID device
        try:
            rfid = RFID.objects.get(sn=sn)
            office = rfid.office
        except RFID.DoesNotExist:
            return Response({'error': 'Invalid RFID SN'}, status=status.HTTP_404_NOT_FOUND)

        time_obj = datetime.fromisoformat(time_stamp)
        time_obj = time_obj.replace(microsecond=0)

        # SAFE get_or_create
        pilgrim, created = safe_get_or_create_pilgrim(
            office=office,
            time_obj=time_obj,
            defaults={'rfid_count': rfid_count}
        )

        # If exists → update
        if not created:
            pilgrim.rfid_count = rfid_count

            # Check illegal pilgrims
            if pilgrim.camera_count is not None:
                diff = pilgrim.camera_count - pilgrim.rfid_count
                pilgrim.illegal_pilgrims = diff if diff > 0 else 0

                if pilgrim.illegal_pilgrims == 0 and pilgrim.image:
                    if hasattr(pilgrim.image, 'path') and os.path.exists(pilgrim.image.path):
                        os.remove(pilgrim.image.path)
                    pilgrim.image = None

            pilgrim.save()

        serializer = PilgrimSerializer(pilgrim, context={"request": request})
        return Response({"message": "RFID data processed.", "data": serializer.data},
                        status=status.HTTP_201_CREATED)
"""
        
        
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
    
    
class PilgrimFramesAPIView(APIView):
    """
    Returns illegal pilgrim frames based only on tent (office) id.
    URL: /pilgrims/pilgrim-frames/?tent_ids=1&page=1&page_size=30
    """

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