from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.activity_log import log_activity
from app.database import supabase_admin
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Notices"],
)


# ============================================================
# Constants
# ============================================================

DEFAULT_EXPIRATION_HOURS = 24


# ============================================================
# Request Models
# ============================================================

class NoticeCreateRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    # If omitted, notice expires after 24 hours.
    expires_at: datetime | None = None


class NoticeUpdateRequest(BaseModel):
    message: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )

    # Three possible meanings:
    #
    # omitted -> don't change expiration
    # timestamp -> set new expiration
    # null -> remove expiration
    #
    expires_at: datetime | None = None


# ============================================================
# Validation
# ============================================================

def validate_expires_at(expires_at: datetime | None):
    """
    Validate a supplied expiration timestamp.

    The timestamp must:
    - contain timezone information
    - be in the future
    """

    if expires_at is None:
        return

    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        raise HTTPException(
            status_code=400,
            detail="expires_at must include a timezone",
        )

    now = datetime.now(timezone.utc)

    if expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="expires_at must be in the future",
        )


# ============================================================
# CREATE NOTICE
# ============================================================

@router.post("/notices")
def create_notice(
    data: NoticeCreateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        # -----------------------------------------------------
        # 1. Determine expiration
        # -----------------------------------------------------

        if data.expires_at is None:
            expires_at = (
                datetime.now(timezone.utc)
                + timedelta(hours=DEFAULT_EXPIRATION_HOURS)
            )
        else:
            validate_expires_at(data.expires_at)
            expires_at = data.expires_at

        # -----------------------------------------------------
        # 2. Create notice
        # -----------------------------------------------------

        notice_data = {
            "pandal_id": pandal_id,
            "message": data.message,
            "expires_at": expires_at.isoformat(),
        }

        result = (
            supabase_admin
            .table("pandal_notices")
            .insert(notice_data)
            .execute()
        )

        if not result or not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create notice",
            )

        notice = result.data[0]

        # -----------------------------------------------------
        # 3. Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="CREATE",
            entity_type="NOTICE",
            entity_id=notice["id"],
            old_value=None,
            new_value={
                "message": data.message,
                "expires_at": expires_at.isoformat(),
            },
            request=request,
        )

        # -----------------------------------------------------
        # 4. Response
        # -----------------------------------------------------

        return {
            "message": "Notice created successfully",
            "notice": notice,
        }

    except HTTPException:
        raise

    except Exception as e:
        print("NOTICE CREATE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to create notice",
        )


# ============================================================
# GET NOTICES
# ============================================================

@router.get("/notices")
def get_notices(
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        result = (
            supabase_admin
            .table("pandal_notices")
            .select(
                "id, message, expires_at, "
                "created_by_device_id, created_at"
            )
            .eq("pandal_id", pandal_id)
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "pandal_id": pandal_id,
            "notices": result.data or [],
        }

    except Exception as e:
        print("NOTICE GET ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch notices",
        )


# ============================================================
# UPDATE NOTICE
# ============================================================

@router.put("/notices/{notice_id}")
def update_notice(
    notice_id: UUID,
    data: NoticeUpdateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        # -----------------------------------------------------
        # 1. Verify notice belongs to this pandal
        # -----------------------------------------------------

        existing = (
            supabase_admin
            .table("pandal_notices")
            .select("id, message, expires_at")
            .eq("id", str(notice_id))
            .eq("pandal_id", pandal_id)
            .maybe_single()
            .execute()
        )

        if not existing or not existing.data:
            raise HTTPException(
                status_code=404,
                detail="Notice not found",
            )

        # -----------------------------------------------------
        # 2. Build update
        # -----------------------------------------------------

        update_data = {}

        if data.message is not None:
            update_data["message"] = data.message

        # -----------------------------------------------------
        # Expiration handling
        #
        # Since Pydantic cannot distinguish between:
        #
        #   "expires_at" omitted
        #
        # and
        #
        #   "expires_at": null
        #
        # we inspect the fields explicitly.
        # -----------------------------------------------------

        if "expires_at" in data.model_fields_set:

            if data.expires_at is None:
                # Explicit null = remove expiration
                update_data["expires_at"] = None

            else:
                validate_expires_at(data.expires_at)

                update_data["expires_at"] = (
                    data.expires_at.isoformat()
                )

        # -----------------------------------------------------
        # 3. Make sure something was actually supplied
        # -----------------------------------------------------

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided",
            )

        # -----------------------------------------------------
        # 4. Update database
        # -----------------------------------------------------

        result = (
            supabase_admin
            .table("pandal_notices")
            .update(update_data)
            .eq("id", str(notice_id))
            .eq("pandal_id", pandal_id)
            .execute()
        )

        if not result or not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update notice",
            )

        # -----------------------------------------------------
        # 5. Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="UPDATE",
            entity_type="NOTICE",
            entity_id=str(notice_id),
            old_value=None,
            new_value=update_data,
            request=request,
        )

        # -----------------------------------------------------
        # 6. Response
        # -----------------------------------------------------

        return {
            "message": "Notice updated successfully",
            "notice": result.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        print("NOTICE UPDATE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to update notice",
        )


# ============================================================
# DELETE NOTICE
# ============================================================

@router.delete("/notices/{notice_id}")
def delete_notice(
    notice_id: UUID,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        result = (
            supabase_admin
            .table("pandal_notices")
            .delete()
            .eq("id", str(notice_id))
            .eq("pandal_id", pandal_id)
            .execute()
        )

        if not result or not result.data:
            raise HTTPException(
                status_code=404,
                detail="Notice not found",
            )

        # -----------------------------------------------------
        # Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="DELETE",
            entity_type="NOTICE",
            entity_id=str(notice_id),
            old_value=None,
            new_value=None,
            request=request,
        )

        return {
            "message": "Notice deleted successfully",
            "notice_id": str(notice_id),
        }

    except HTTPException:
        raise

    except Exception as e:
        print("NOTICE DELETE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to delete notice",
        )