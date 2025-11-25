from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import render, get_object_or_404
from .models import Office
from .serializers import OfficeSerializer
#from pilgrims.models import Pilgrim
from django.db.models import Sum
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive, is_aware
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


def to_aware_riyadh(dt):
    if dt is None:
        return None

    # If string has no timezone, treat it as Saudi time
    if dt.tzinfo is None:
        return saudi_tz.localize(dt)

    # Otherwise convert to Riyadh zone
    return dt.astimezone(saudi_tz)

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


"""
class DashboardIllegalPilgrims(APIView):
    permission_classes = []  # <-- keep or replace based on your security

    def get(self, request):

        # Extract params
        office_list = request.GET.get("tent_list", None)
        is_live = request.GET.get("is_live", "false").lower() == "true"
        start_raw = request.GET.get("start_date_time")
        end_raw = request.GET.get("end_date_time")
        user_provided_date = start_raw and end_raw
        
        user = request.user

        # ✅ Base query: only user's company offices
        if user.is_admin:
            offices = Office.objects.filter(company=user.company)
        else:
            assigned_ids = user.assigned_office.values_list('id', flat=True)
            offices = Office.objects.filter(id__in=assigned_ids, company=user.company)

        # ✅ Optional tent_list filter
        if office_list:
            try:
                office_ids = [int(t) for t in office_list.split(",") if t.strip().isdigit()]
                offices = offices.filter(id__in=office_ids)
            except ValueError:
                return Response({"detail": "Invalid tent_list format"}, status=400)

        if is_live:
            end_date_time = timezone.now().astimezone(saudi_tz)
            start_date_time = end_date_time - timezone.timedelta(minutes=30)

        else:
            start_date_time = to_aware_riyadh(parse_datetime(start_raw)) if start_raw else None
            end_date_time = to_aware_riyadh(parse_datetime(end_raw)) if end_raw else None
        results = []

        for office in offices:
            if user_provided_date:
                filtered_entries = Pilgrim.objects.filter(
                    office=office,
                    time_stamp__gte=start_date_time,
                    time_stamp__lte=end_date_time,
                )
            else:
                filtered_entries = Pilgrim.objects.filter(office=office)

            total_detect_by_camera = filtered_entries.aggregate(total=Sum("camera_count"))["total"] or 0
            total_detect_by_rfid = filtered_entries.aggregate(total=Sum("rfid_count"))["total"] or 0
            total_people = max(total_detect_by_camera, total_detect_by_rfid)
            total_illegal_pilgrims = filtered_entries.aggregate(total=Sum("illegal_pilgrims"))["total"] or 0

            indicator = "red" if total_illegal_pilgrims > 0 else "green"

            results.append({
                "tent_id": office.id,
                "tent_name": office.name,
                "illegal_pilgrims": total_illegal_pilgrims,
                "total_people": total_people,
                "indicator": indicator,
                "is_sensor_available": True,
            })

        return Response(
            {
                "success": True,
                "message": "Dashboard Illegal Pilgrims Data",
                "start_date_time": start_date_time,
                "end_date_time": end_date_time,
                "results": results,
            },
            status=status.HTTP_200_OK,
        )"""