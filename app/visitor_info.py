from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.activity_log import log_activity
from app.database import supabase_admin
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Visitor Information"],
)


class VisitorInfoRequest(BaseModel):
    entry_information: str | None = Field(
        default=None,
        max_length=2000,
    )
    parking_information: str | None = Field(
        default=None,
        max_length=2000,
    )
    accessibility_information: str | None = Field(
        default=None,
        max_length=2000,
    )


@router.get("/visitor-info")
def get_visitor_info(
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        result = (
            supabase_admin
            .table("pandal_visitor_info")
            .select(
                "pandal_id, entry_information, "
                "parking_information, accessibility_information, "
                "updated_at"
            )
            .eq("pandal_id", pandal_id)
            .maybe_single()
            .execute()
        )

        if not result.data:
            return {
                "pandal_id": pandal_id,
                "visitor_info": None,
            }

        return {
            "pandal_id": pandal_id,
            "visitor_info": result.data,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch visitor information",
        )


@router.put("/visitor-info")
def update_visitor_info(
    data: VisitorInfoRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        visitor_data = {
            "pandal_id": pandal_id,
            "entry_information": data.entry_information,
            "parking_information": data.parking_information,
            "accessibility_information": data.accessibility_information,
            "updated_at": datetime.now().astimezone().isoformat(),
        }

        # -----------------------------------------------------
        # 1. Create or update visitor information
        # -----------------------------------------------------

        result = (
            supabase_admin
            .table("pandal_visitor_info")
            .upsert(
                visitor_data,
                on_conflict="pandal_id",
            )
            .execute()
        )

        if not result or not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update visitor information",
            )

        # -----------------------------------------------------
        # 2. Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="UPDATE",
            entity_type="VISITOR_INFO",
            entity_id=None,
            old_value=None,
            new_value={
                "entry_information": data.entry_information,
                "parking_information": data.parking_information,
                "accessibility_information": data.accessibility_information,
            },
            request=request,
        )

        # -----------------------------------------------------
        # 3. Return response
        # -----------------------------------------------------

        return {
            "message": "Visitor information updated successfully",
            "visitor_info": result.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        print("VISITOR INFO UPDATE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to update visitor information",
        )