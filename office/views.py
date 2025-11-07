from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import render, get_object_or_404
from .models import Office
from .serializers import OfficeSerializer
from pilgrims.models import Pilgrim
from django.db.models import Sum
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_aware
import pytz
from django.utils import timezone
from datetime import datetime, time

saudi_tz = pytz.timezone('Asia/Riyadh')


def Current_saudi_time():
    now_saudi = timezone.now().astimezone(saudi_tz)
    start_time = saudi_tz.localize(
        datetime.combine(now_saudi.date(), time.min))
    end_time = now_saudi

    return start_time, end_time

import re

def tent_name_list_dict_sorting(s):
    """Helper for natural sorting (e.g., 2 before 10, '71-1' before '71-2')."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def date_time_to_aware(date_time):
    if not is_aware(date_time):
        date_time = make_aware(date_time)
    return date_time
class CustomPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allow clients to set their own page size
    max_page_size = 100  # Limit the maximum page size
    
class OfficeApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        user = request.user
        company_ids_qr = request.GET.get('company_ids', '')

        # Parse ID list
        def parse_id_list(param: str) -> list[int]:
            return [int(i) for i in param.split(',') if i.strip().isdigit()]

        company_ids = parse_id_list(company_ids_qr)

        if pk:
            # Single tent/office detail
            tent = get_object_or_404(Office, pk=pk)

            if tent.company != request.user.company:
                return Response({
                    "success": False,
                    "message": f"Office/Tent with ID {pk} does not belong to your company."
                }, status=status.HTTP_403_FORBIDDEN)

            if not user.is_admin and tent not in user.assigned_tent.all():
                return Response({
                    "success": False,
                    "message": f"Office/Tent with ID {pk} is not assigned to you."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = OfficeSerializer(tent, context={'request': request})
            return Response({
                "success": True,
                "data": serializer.data
            })

        elif company_ids and user.is_annotator:
            queryset = Office.objects.filter(company__id__in=company_ids)
            queryset = sorted(queryset, key=lambda tent: tent_name_list_dict_sorting(tent.name))
            serializer = OfficeSerializer(queryset, many=True, context={'request': request})
            return Response({
                "success": True,
                "results": serializer.data
            })

        else:
            # List all tents/offices based on user role
            paginate = request.query_params.get('paginate', 'false').lower() == 'true'

            if user.is_admin:
                queryset = Office.objects.filter(company=request.user.company)
            else:
                assigned_tent_ids = user.assigned_tent.values_list('id', flat=True)
                queryset = Office.objects.filter(id__in=assigned_tent_ids, company=request.user.company)

            queryset = sorted(queryset, key=lambda tent: tent_name_list_dict_sorting(tent.name))

            if paginate:
                paginator = CustomPagination()
                paginated_queryset = paginator.paginate_queryset(queryset, request)
                serializer = OfficeSerializer(paginated_queryset, many=True, context={'request': request})
                return paginator.get_paginated_response(serializer.data)

            serializer = OfficeSerializer(queryset, many=True, context={'request': request})
            return Response({
                "success": True,
                "results": serializer.data
            })



class DashboardIllegalPilgrims(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # GET parameters with defaults and normalization
        #is_arafa = request.GET.get("is_arafa", "false").lower() == "true"
        nationality_param = request.GET.get("nationality", "all")
        office_list = request.GET.get("tent_list", None)

        user = request.user
        # Base queryset
        offices = Office.objects.all()

        # Parse nationality filter
        if nationality_param.lower() != "all":
            try:
                nationality_ids = [int(x) for x in nationality_param.split(
                    ',') if x.strip().isdigit()]
            except ValueError:
                return Response({"detail": "Invalid nationality list."}, status=400)
        else:
            nationality_ids = []
        # Filter by tent_list if provided
        if office_list:
            try:
                office_ids = [int(tid) for tid in office_list.split(
                    ',') if tid.strip().isdigit()]
                offices = offices.filter(id__in=office_ids)
            except ValueError:
                return Response({"detail": "Invalid office_id list."}, status=400)
        else:
            if user.is_admin:
                offices = offices.filter(company=user.company)
            else:
                assigned_ids = user.assigned_office.values_list('id', flat=True)
                offices = offices.filter(id__in=assigned_ids, company=user.company)
            # Filter by nationality if it's not 'all'
            if nationality_ids:
                offices = offices.filter(nationality__id__in=nationality_ids)

        def get_aware_datetime_from_str(date_str):
            if not date_str:
                return None
            dt = parse_datetime(date_str)
            if dt is not None:
                return date_time_to_aware(dt)
            return None

        is_live = request.GET.get('is_live', 'false').lower() == 'true'

        if is_live:
            start_date_time, end_date_time = Current_saudi_time()
        else:
            start_date_time = get_aware_datetime_from_str(
                request.GET.get('start_date_time')) or timezone.now()
            end_date_time = get_aware_datetime_from_str(
                request.GET.get('end_date_time')) or timezone.now()

        results = []
        for office in offices:

            filtered_entries = Pilgrim.objects.filter(
                office=office,
                time_stamp__gte=start_date_time,
                time_stamp__lte=end_date_time
            )
            total_detect_by_camera = filtered_entries.aggregate(
                total=Sum('camera_count'))['total'] or 0
            total_illegal_pilgrims = filtered_entries.aggregate(
                total=Sum('illegal_pilgrims'))['total'] or 0
            
            indicator = "green"
            if total_illegal_pilgrims > 0:
                indicator = "red"

            results.append({
                "tent_id": office.id,
                "tent_name": office.name,
                "illegal_pilgrims": total_illegal_pilgrims,
                "total_people": total_detect_by_camera,
                "indicator": indicator,
                "is_sensor_available": True
            })

        results.sort(key=lambda x: tent_name_list_dict_sorting(x["tent_name"]))
        return Response({
            "success": True,
            "message": "Dashboard Illegal Pilgrims Data",
            "results": results
        }, status=status.HTTP_200_OK)

