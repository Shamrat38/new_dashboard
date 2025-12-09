from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
import pytz
import os

from .models import CameraCounter, RFIDCounter, Pilgrim

saudi_tz = pytz.timezone("Asia/Riyadh")


# ------------------------------------------------------
# FIRST STAGE — ALWAYS CREATE ROW
# ------------------------------------------------------
def _merge_for_timestamp(target_ts):
    """
    ALWAYS creates a Pilgrim row for the timestamp.
    No updates, no get_or_create — only create().
    """

    target_ts = target_ts.replace(microsecond=0)

    camera = (
        CameraCounter.objects.filter(time_stamp=target_ts)
        .order_by("-id")
        .first()
    )
    rfid = (
        RFIDCounter.objects.filter(time_stamp=target_ts)
        .order_by("-id")
        .first()
    )

    # If no camera & no RFID — cannot determine office → skip
    if not camera and not rfid:
        return

    # Determine office_id
    office_id = camera.office_id if camera else rfid.office_id

    camera_count = camera.camera_count if camera else None
    rfid_count = rfid.rfid_count if rfid else None
    image = camera.image if (camera and camera.image) else None

    # Compute illegal pilgrims
    if camera_count is not None and rfid_count is not None:
        illegal = max(camera_count - rfid_count, 0)
    else:
        illegal = 0

    # Always create a new row (never update here)
    Pilgrim.objects.create(
        office_id=office_id,
        time_stamp=target_ts,
        camera_count=camera_count,
        rfid_count=rfid_count,
        illegal_pilgrims=illegal,
        image=image if illegal > 0 else None,
    )


# ------------------------------------------------------
# SECOND STAGE — UPDATE ONLY, NEVER CREATE
# ------------------------------------------------------
def _check_for_timestamp(target_ts):
    """
    Only update existing Pilgrim row.
    Never create a new row here — if missing, just ignore.
    """

    target_ts = target_ts.replace(microsecond=0)

    # Fetch existing row
    pilgrim = Pilgrim.objects.filter(time_stamp=target_ts).first()
    if not pilgrim:
        return  # Do NOT create anything here — merge only happens in first stage

    # Fetch latest camera & RFID rows
    camera = (
        CameraCounter.objects.filter(time_stamp=target_ts)
        .order_by("-id")
        .first()
    )
    rfid = (
        RFIDCounter.objects.filter(time_stamp=target_ts)
        .order_by("-id")
        .first()
    )

    updated = False

    # ------------------------
    # FILL missing values only
    # ------------------------
    if pilgrim.camera_count is None and camera:
        pilgrim.camera_count = camera.camera_count
        updated = True

    if pilgrim.rfid_count is None and rfid:
        pilgrim.rfid_count = rfid.rfid_count
        updated = True

    # Recalc illegal
    if pilgrim.camera_count is not None and pilgrim.rfid_count is not None:
        pilgrim.illegal_pilgrims = max(
            pilgrim.camera_count - pilgrim.rfid_count, 0
        )
    else:
        pilgrim.illegal_pilgrims = 0

    # Update image logic
    if pilgrim.illegal_pilgrims > 0:
        if camera and camera.image:
            pilgrim.image = camera.image
    else:
        # remove image when illegal = 0
        if pilgrim.image:
            try:
                if hasattr(pilgrim.image, "path") and os.path.exists(pilgrim.image.path):
                    os.remove(pilgrim.image.path)
            except:
                pass
            pilgrim.image = None

    if updated:
        pilgrim.save()


# ------------------------------------------------------
# MAIN CELERY BEAT TASK — RUNS EVERY SECOND
# ------------------------------------------------------
@shared_task
def merge_pilgrims_every_second():
    """
    Runs every second:
    1. Create row for NOW - 5 seconds
    2. Update row for NOW - 5 minutes
    3. Update row for NOW - 10 minutes
    """

    now_saudi = timezone.now().astimezone(saudi_tz).replace(microsecond=0)

    ts_5s = now_saudi - timedelta(seconds=5)
    ts_5m = now_saudi - timedelta(minutes=5)
    ts_10m = now_saudi - timedelta(minutes=10)

    # First stage: ALWAYS create row
    _merge_for_timestamp(ts_5s)

    # Second stage: ONLY update row
    _check_for_timestamp(ts_5m)
    _check_for_timestamp(ts_10m)
