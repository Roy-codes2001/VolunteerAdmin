from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.activity_log import log_activity
from app.database import supabase_admin
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


class CrowdLevel(str, Enum):
    low = "LOW"
    moderate = "MODERATE"
    high = "HIGH"
    very_high = "VERY_HIGH"


class RainStatus(str, Enum):
    clear = "CLEAR"
    light = "LIGHT"
    heavy = "HEAVY"


class EntryStatus(str, Enum):
    open = "OPEN"
    closed = "CLOSED"


class QuickUpdateRequest(BaseModel):
    crowd_level: CrowdLevel
    rain_status: RainStatus
    entry_status: EntryStatus
    wait_time_minutes: int = Field(
        ge=0,
        le=999,
    )


@router.post("/quick-update")
def quick_update(
    data: QuickUpdateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        # -----------------------------------------------------
        # 1. Update live status
        # -----------------------------------------------------

        result = (
            supabase_admin
            .table("pandal_live_status")
            .upsert(
                {
                    "pandal_id": pandal_id,
                    "crowd_level": data.crowd_level.value,
                    "rain_status": data.rain_status.value,
                    "entry_status": data.entry_status.value,
                    "wait_time_minutes": data.wait_time_minutes,
                },
                on_conflict="pandal_id",
            )
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update live status",
            )

        # -----------------------------------------------------
        # 2. Write activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="UPDATE",
            entity_type="LIVE_STATUS",
            old_value=None,
            new_value={
                "crowd_level": data.crowd_level.value,
                "rain_status": data.rain_status.value,
                "entry_status": data.entry_status.value,
                "wait_time_minutes": data.wait_time_minutes,
            },
            request=request,
        )

        # -----------------------------------------------------
        # 3. Return response
        # -----------------------------------------------------

        return {
            "message": "Live status updated successfully",
            "pandal_id": pandal_id,
            "status": result.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        print("QUICK UPDATE ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )