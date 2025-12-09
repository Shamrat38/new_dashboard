from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Pilgrim, CameraCounter, RFIDCounter, Office
from django.db.models import Q

@shared_task
def process_pilgrims_data():
    now = timezone.now()

    # Times to check
    time_5s = now - timedelta(seconds=5)
    time_5m = now - timedelta(minutes=5)
    time_10m = now - timedelta(minutes=10)

    # Run Stage 1 (create)
    run_stage_1(time_5s)

    # Run Stage 2 (update missing)
    run_stage_2(time_5m)
    run_stage_2(time_10m)


def run_stage_1(target_time):
    offices = Office.objects.all()

    for office in offices:

        # 1. Check if already created
        pilgrim, created = Pilgrim.objects.get_or_create(
            office=office,
            time_stamp=target_time,
            defaults={
                "camera_count": None,
                "rfid_count": None,
                "image": None,
            }
        )

        # If exists already → do not recreate
        # But still fill missing values if available
        update_from_sources(pilgrim)


def run_stage_2(target_time):
    """Recheck old rows and update missing fields."""
    pilgrims = Pilgrim.objects.filter(time_stamp=target_time)

    for pilgrim in pilgrims:
        update_from_sources(pilgrim)


def update_from_sources(pilgrim):
    """Fill missing values from CameraCounter / RFIDCounter."""
    office = pilgrim.office
    timestamp = pilgrim.time_stamp

    # --- CAMERA ---
    if pilgrim.camera_count is None or pilgrim.image in [None, ""]:
        cam = CameraCounter.objects.filter(
            office=office,
            time_stamp=timestamp
        ).first()

        if cam:
            if pilgrim.camera_count is None:
                pilgrim.camera_count = cam.camera_count
            if (not pilgrim.image) and cam.image:
                pilgrim.image = cam.image

    # --- RFID ---
    if pilgrim.rfid_count is None:
        rfid = RFIDCounter.objects.filter(
            office=office,
            time_stamp=timestamp
        ).first()

        if rfid:
            pilgrim.rfid_count = rfid.rfid_count

    pilgrim.save()
