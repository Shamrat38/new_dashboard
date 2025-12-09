from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.db.models.functions import TruncSecond
import pytz
import os

from .models import CameraCounter, RFIDCounter, Pilgrim

saudi_tz = pytz.timezone("Asia/Riyadh")


# -------------------------------
# NORMALIZED MERGE HELPER
# -------------------------------
def _merge_for_timestamp(target_ts):
    """
    Merge data for EXACT second (no microseconds).
    Uses TruncSecond to match DB rows correctly.
    """

    target_ts = target_ts.replace(microsecond=0)

    # Normalize DB timestamps using TruncSecond
    camera_qs = (
        CameraCounter.objects
        .annotate(ts_trim=TruncSecond("time_stamp"))
        .filter(ts_trim=target_ts)
        .order_by("-id")
    )

    rfid_qs = (
        RFIDCounter.objects
        .annotate(ts_trim=TruncSecond("time_stamp"))
        .filter(ts_trim=target_ts)
        .order_by("-id")
    )

    # If nothing exists for this second → ignore
    if not camera_qs.exists() and not rfid_qs.exists():
        return

    # Collect all offices involved for this second
    office_ids = set(camera_qs.values_list("office_id", flat=True)).union(
        set(rfid_qs.values_list("office_id", flat=True))
    )

    for office_id in office_ids:
        cam = camera_qs.filter(office_id=office_id).first()
        rfd = rfid_qs.filter(office_id=office_id).first()

        camera_count = cam.camera_count if cam else None
        rfid_count = rfd.rfid_count if rfd else None
        image = cam.image if cam and cam.image else None

        # Calculate illegal pilgrims
        illegal = 0
        if camera_count is not None and rfid_count is not None:
            diff = camera_count - rfid_count
            illegal = diff if diff > 0 else 0

        # UPSERT INTO PILGRIM TABLE
        with transaction.atomic():
            pilgrim, created = Pilgrim.objects.get_or_create(
                office_id=office_id,
                time_stamp=target_ts,  # IMPORTANT → ALWAYS normalized timestamp
                defaults={
                    "camera_count": camera_count,
                    "rfid_count": rfid_count,
                    "illegal_pilgrims": illegal,
                    "image": image,
                }
            )

            if not created:
                # Update missing fields
                if camera_count is not None:
                    pilgrim.camera_count = camera_count

                if rfid_count is not None:
                    pilgrim.rfid_count = rfid_count

                # Recalculate illegal
                if pilgrim.camera_count is not None and pilgrim.rfid_count is not None:
                    diff = pilgrim.camera_count - pilgrim.rfid_count
                    pilgrim.illegal_pilgrims = diff if diff > 0 else 0

                # Image logic
                if pilgrim.illegal_pilgrims > 0:
                    if image:
                        pilgrim.image = image
                else:
                    # No illegal → remove image
                    if pilgrim.image:
                        try:
                            if hasattr(pilgrim.image, "path") and os.path.exists(pilgrim.image.path):
                                os.remove(pilgrim.image.path)
                        except:
                            pass
                        pilgrim.image = None

                pilgrim.save()


# -------------------------------
# CELERY TASK RUNNING EVERY SECOND
# -------------------------------
@shared_task
def merge_pilgrims_every_second():
    now_saudi = timezone.now().astimezone(saudi_tz).replace(microsecond=0)

    timestamps = [
        now_saudi - timedelta(seconds=5),     # Stage 1
        now_saudi - timedelta(minutes=5),     # Stage 2
        now_saudi - timedelta(minutes=10),    # Stage 3
    ]

    for ts in timestamps:
        _merge_for_timestamp(ts)
