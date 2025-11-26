from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import F
import pytz
import os

from .models import CameraCounter, RFIDCounter, Pilgrim

saudi_tz = pytz.timezone("Asia/Riyadh")


def _merge_for_timestamp(target_ts):
    """
    Merge data for *one* exact timestamp (second precision)
    from CameraCounter + RFIDCounter into Pilgrim.

    - If Pilgrim row exists → update missing fields.
    - If not → create.
    - Recalculate illegal_pilgrims.
    """

    # Ensure no microsecond noise
    target_ts = target_ts.replace(microsecond=0)

    # Get all rows at this exact second
    camera_qs = CameraCounter.objects.filter(time_stamp=target_ts)
    rfid_qs = RFIDCounter.objects.filter(time_stamp=target_ts)

    if not camera_qs.exists() and not rfid_qs.exists():
        # Nothing to merge for this second
        return

    # Collect all offices that have either camera or RFID data at this timestamp
    camera_offices = set(camera_qs.values_list("office_id", flat=True))
    rfid_offices = set(rfid_qs.values_list("office_id", flat=True))
    office_ids = camera_offices.union(rfid_offices)

    for office_id in office_ids:
        # Pick the latest record for that office & timestamp (if there are multiple)
        camera = (
            camera_qs.filter(office_id=office_id)
            .order_by("-id")
            .first()
        )
        rfid = (
            rfid_qs.filter(office_id=office_id)
            .order_by("-id")
            .first()
        )

        camera_count = camera.camera_count if camera else None
        rfid_count = rfid.rfid_count if rfid else None
        image = camera.image if camera and camera.image else None

        # If both counts are missing, nothing to do
        if camera_count is None and rfid_count is None:
            continue

        # Calculate illegal_pilgrims (if both sides available)
        illegal = 0
        if camera_count is not None and rfid_count is not None:
            diff = camera_count - rfid_count
            illegal = diff if diff > 0 else 0

        # UPSERT into Pilgrim
        with transaction.atomic():
            pilgrim, created = Pilgrim.objects.get_or_create(
                office_id=office_id,
                time_stamp=target_ts,
                defaults={
                    "camera_count": camera_count,
                    "rfid_count": rfid_count,
                    "illegal_pilgrims": illegal,
                    "image": image,
                },
            )

            if not created:
                # Fill / update fields if we have new data
                if camera_count is not None:
                    pilgrim.camera_count = camera_count
                if rfid_count is not None:
                    pilgrim.rfid_count = rfid_count

                # Recalculate illegal only if both counts exist
                if pilgrim.camera_count is not None and pilgrim.rfid_count is not None:
                    diff = pilgrim.camera_count - pilgrim.rfid_count
                    pilgrim.illegal_pilgrims = diff if diff > 0 else 0

                # Image logic
                if pilgrim.illegal_pilgrims > 0:
                    # Keep / overwrite with latest image if we have one
                    if image:
                        pilgrim.image = image
                else:
                    # No illegal → delete image if exists
                    if pilgrim.image:
                        try:
                            if hasattr(pilgrim.image, "path") and os.path.exists(
                                pilgrim.image.path
                            ):
                                os.remove(pilgrim.image.path)
                        except Exception:
                            # Ignore OS errors
                            pass
                        pilgrim.image = None

                pilgrim.save()


@shared_task
def merge_pilgrims_every_second():
    """
    Runs every second via Celery Beat.

    For current Saudi time NOW:
      - Stage 1: process timestamp = NOW - 5 seconds
      - Stage 2: recheck timestamp = NOW - 5 minutes
      - Stage 3: recheck timestamp = NOW - 10 minutes

    Each call only processes those three exact seconds
    (so each 'second' in history gets up to 3 chances to be merged).
    """

    now_saudi = timezone.now().astimezone(saudi_tz).replace(microsecond=0)

    # Stage 1: 5 seconds ago
    ts_5s = now_saudi - timedelta(seconds=5)

    # Stage 2: 5 minutes ago
    ts_5m = now_saudi - timedelta(minutes=5)

    # Stage 3: 10 minutes ago
    ts_10m = now_saudi - timedelta(minutes=10)

    # Process each timestamp
    _merge_for_timestamp(ts_5s)
    _merge_for_timestamp(ts_5m)
    _merge_for_timestamp(ts_10m)
