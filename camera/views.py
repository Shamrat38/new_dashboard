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
from camera.models import Camera, CounterHistory
from authentication.permissions import PeopleCountPermission
from office.models import Office

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

def convert_utc_to_riyadh(utc_dt):
    """
    Convert a UTC datetime to Riyadh (Asia/Riyadh) timezone.

    Parameters:
        utc_dt (datetime): A timezone-aware or naive UTC datetime object.

    Returns:
        datetime: A timezone-aware datetime object in Riyadh timezone.
    """
    if utc_dt.tzinfo is None:
        # Assume input is in UTC if naive
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(saudi_tz)
def start_end_time_to_riyad(dt):
    if dt.tzinfo is None:
        return saudi_tz.localize(dt)
    return dt.astimezone(saudi_tz)

class PeopleCountingCardView(APIView):
    permission_classes = [PeopleCountPermission]

    def get(self, request):
        user = request.user
        """
        Get counter statistics for all tents or for specific tents if tent_ids are provided.
        Optionally filter by date range using start_date_time and end_date_time.
        """
        office_ids = request.query_params.get('office_ids')
        start_date_time_str = request.GET.get('start_date_time')
        end_date_time_str = request.GET.get('end_date_time')

        start_date_time = parse_datetime(start_date_time_str) if isinstance(
            start_date_time_str, str) else None
        end_date_time = parse_datetime(end_date_time_str) if isinstance(
            end_date_time_str, str) else None

        if not start_date_time or not end_date_time:
            start_date_time, end_date_time = Current_saudi_time()

        offices = None

        if user.is_admin:
            offices = Office.objects.filter(
                company=request.user.company)
        else:
            assigned_tent_ids = user.assigned_tent.values_list(
                'id', flat=True)
            offices = Office.objects.filter(
                id__in=assigned_tent_ids, company=request.user.company)
        if office_ids:
            try:
                office_id_list = [int(tid.strip()) for tid in office_ids.split(
                    ',') if tid.strip().isdigit()]
                offices = offices.filter(id__in=office_id_list)
            except ValueError:
                return Response({"error": "Invalid tent_ids format. Use comma-separated integers."}, status=400)

        result = []

        for office in offices:
            last_update = None
            cameras = Camera.objects.filter(office=office, type="peoplecount")

            # print(end_date_time)

            counter_history_query = CounterHistory.objects.filter(
                camera__in=cameras,
                end_time__lte=end_date_time)
            count = counter_history_query.count()

            # if end_date_time:
            #     counter_history_query = counter_history_query.filter(
            #         end_time__lte=end_date_time
            #     )

            if counter_history_query:
                last_update = counter_history_query.order_by(
                    "-end_time").first().end_time or None

            aggregates = counter_history_query.aggregate(
                total=Sum('total'),
                total_in=Sum('total_in'),
                total_out=Sum('total_out')
            )

            total_in = aggregates.get('total_in') or 0
            total_out = aggregates.get('total_out') or 0
            # Ensure total_out is not greater than total_in
            if total_out > total_in:
                total_out = total_in

            current_staying = total_in - total_out
            if total_in is None:
                total_in = 0
            if total_out is None:
                total_out = 0
            if current_staying is None:
                current_staying = 0
            current_percentage = round(
                (current_staying / office.capacity) * 100, 2) if office.capacity else 0.00

            tent_data = {
                'id': office.id,
                'name': office.name,
                'capacity': office.capacity,
                'total_in': total_in,
                'total_out': total_out,
                'current_staying': current_staying,
                'current_percentage': current_percentage,
                'last_update': convert_utc_to_riyadh(last_update) if last_update else last_update,
                "count": count
            }

            result.append(tent_data)

        # serializer = TentCounterSerializer(result, many=True)
        return Response({
            "success": True,
            "message": "Camera list fetched successfully.",
            "start_date_time": start_date_time,
            "end_date_time": end_date_time,
            "results": result
        }, status=status.HTTP_200_OK)


class PeopleGraphView(APIView):
    permission_classes = [PeopleCountPermission]

    def get(self, request):
        user = request.user
        office_ids = request.query_params.get('office_ids')
        start_date_time_str = request.GET.get('start_date_time')
        # start_date_time_str = start_date_time_str.replace(' ', 'T')
        end_date_time_str = request.GET.get('end_date_time')
        # end_date_time_str = end_date_time_str.replace(' ', 'T')
        start_date_time = parse_datetime(start_date_time_str) if isinstance(
            start_date_time_str, str) else None
        end_date_time = parse_datetime(end_date_time_str) if isinstance(
            end_date_time_str, str) else None
        if start_date_time and end_date_time:
            start_date_time = start_end_time_to_riyad(start_date_time)
            end_date_time = start_end_time_to_riyad(end_date_time)

        if not start_date_time or not end_date_time:
            start_date_time, end_date_time = Current_saudi_time()

        offices = None
        if user.is_admin:
            offices = Office.objects.filter(
                company=request.user.company)

        else:
            assigned_office_ids = user.assigned_tent.values_list(
                'id', flat=True)
            tents = Office.objects.filter(
                id__in=assigned_office_ids, company=request.user.company)

        if office_ids:
            try:
                office_id_list = [int(tid.strip()) for tid in office_ids.split(
                    ',') if tid.strip().isdigit()]
                offices = offices.filter(id__in=office_id_list)
            except ValueError:
                return Response({"error": "Invalid tent_ids format. Use comma-separated integers."}, status=400)

        # Generate 30-minute intervals
        # time_labels = []
        # current_time = start_date_time
        # while current_time <= end_date_time:
        #     time_labels.append(current_time)
        #     current_time += timedelta(minutes=5)

        tent_staying_map = []
        initial_aggregate = {}
        initial_total_in = 0
        initial_total_out = 0
        current_staying = 0
        for office in offices:
            cameras = Camera.objects.filter(office=office, type="peoplecount")
            last_data = CounterHistory.objects.filter(
                camera__in=cameras).order_by('-end_time').first()
            # if last_data:
            #     capped_end_time = max(end_date_time, last_data.end_time)
            # else:
            #     capped_end_time = start_date_time  # No data at all

            time_labels = []
            current_time = start_date_time
            while current_time <= end_date_time:
                time_labels.append(current_time)
                current_time += timedelta(minutes=5)
            data = []
            count = 0
            counter_historys = CounterHistory.objects.filter(
                camera__in=cameras, end_time__lt=start_date_time).order_by('end_time')
            count += counter_historys.count()
            # print("counter_history", counter_historys)

            # Initial count before the start date
            initial_aggregate = counter_historys.aggregate(
                total_in=Sum('total_in'), total_out=Sum('total_out'))

            if initial_aggregate is None:
                continue

            initial_total_in = initial_aggregate.get('total_in') or 0
            initial_total_out = initial_aggregate.get('total_out') or 0
            current_staying = initial_total_in - initial_total_out

            # Append initial staying
            data.append(current_staying)
            for i in range(1, len(time_labels)):
                interval_start = time_labels[i - 1]
                interval_end = time_labels[i]
                counter_historys_interval = CounterHistory.objects.filter(
                    camera__in=cameras,
                    end_time__gte=interval_start,
                    end_time__lt=interval_end
                )
                count += counter_historys_interval.count()
                interval_aggregate = counter_historys_interval.aggregate(
                    total_in=Sum('total_in'), total_out=Sum('total_out'))
                total_in = interval_aggregate.get('total_in') or 0
                total_out = interval_aggregate.get('total_out') or 0

                current_staying += (total_in - total_out)
                data.append(current_staying)

            tent_staying_map.append({
                "office_id": office.id,
                "office_name": office.name,
                "office_capacity": office.capacity,
                "count": count,
                "hours": [dt for dt in time_labels],
                "records": data
            })

        return Response({
            "success": True,
            "message": "30-minute interval data per tent fetched successfully.",
            "start_date_time": start_date_time,
            "end_date_time": end_date_time,
            "initial_total_in": initial_total_in,
            "initial_total_out": initial_total_out,

            "results": tent_staying_map
        }, status=status.HTTP_200_OK)
