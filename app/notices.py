from datetime import datetime
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


class NoticeCreateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    expires_at: datetime | None = None


class NoticeUpdateRequest(BaseModel):
    message: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )
    expires_at: datetime | None = None


def validate_expires_at(expires_at: datetime | None):
    if expires_at is not None:
        if expires_at.tzinfo is None or expires_at.utcoffset() is None:
            raise HTTPException(
                status_code=400,
                detail="expires_at must include a timezone",
            )


@router.post("/notices")
def create_notice(
    data: NoticeCreateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    validate_expires_at(data.expires_at)

    try:
        notice_data = {
            "pandal_id": pandal_id,
            "message": data.message,
        }

        if data.expires_at is not None:
            notice_data["expires_at"] = data.expires_at.isoformat()

        result = (
            supabase_admin
            .table("pandal_notices")
            .insert(notice_data)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create notice",
            )

        notice = result.data[0]

        # -----------------------------------------------------
        # Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="CREATE",
            entity_type="NOTICE",
            entity_id=notice["id"],
            old_value=None,
            new_value={
                "message": data.message,
                "expires_at": (
                    data.expires_at.isoformat()
                    if data.expires_at is not None
                    else None
                ),
            },
            request=request,
        )

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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch notices",
        )


@router.put("/notices/{notice_id}")
def update_notice(
    notice_id: UUID,
    data: NoticeUpdateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    validate_expires_at(data.expires_at)

    try:
        # -----------------------------------------------------
        # 1. Verify that the notice belongs to this pandal
        # -----------------------------------------------------

        existing = (
            supabase_admin
            .table("pandal_notices")
            .select("id")
            .eq("id", str(notice_id))
            .eq("pandal_id", pandal_id)
            .maybe_single()
            .execute()
        )

        if not existing.data:
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

        if data.expires_at is not None:
            update_data["expires_at"] = data.expires_at.isoformat()

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided",
            )

        # -----------------------------------------------------
        # 3. Update database
        # -----------------------------------------------------

        result = (
            supabase_admin
            .table("pandal_notices")
            .update(update_data)
            .eq("id", str(notice_id))
            .eq("pandal_id", pandal_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update notice",
            )

        # -----------------------------------------------------
        # 4. Activity log
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

        if not result.data:
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