from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.activity_log import log_activity
from app.database import supabase_admin
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Events"],
)


class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    start_at: datetime
    end_at: datetime


class EventUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    start_at: datetime | None = None
    end_at: datetime | None = None


def validate_event_times(
    start_at: datetime,
    end_at: datetime,
):
    if start_at.tzinfo is None or start_at.utcoffset() is None:
        raise HTTPException(
            status_code=400,
            detail="start_at must include a timezone",
        )

    if end_at.tzinfo is None or end_at.utcoffset() is None:
        raise HTTPException(
            status_code=400,
            detail="end_at must include a timezone",
        )

    if end_at <= start_at:
        raise HTTPException(
            status_code=400,
            detail="Event end time must be after start time",
        )


@router.post("/events")
def create_event(
    data: EventCreateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    validate_event_times(
        data.start_at,
        data.end_at,
    )

    try:
        result = (
            supabase_admin
            .table("pandal_events")
            .insert(
                {
                    "pandal_id": pandal_id,
                    "title": data.title,
                    "description": data.description,
                    "start_at": data.start_at.isoformat(),
                    "end_at": data.end_at.isoformat(),
                }
            )
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create event",
            )

        event = result.data[0]

        # -----------------------------------------------------
        # Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="CREATE",
            entity_type="EVENT",
            entity_id=event["id"],
            old_value=None,
            new_value={
                "title": data.title,
                "description": data.description,
                "start_at": data.start_at.isoformat(),
                "end_at": data.end_at.isoformat(),
            },
            request=request,
        )

        return {
            "message": "Event created successfully",
            "event": event,
        }

    except HTTPException:
        raise

    except Exception as e:
        print("EVENT CREATE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to create event",
        )


@router.get("/events")
def get_events(
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        result = (
            supabase_admin
            .table("pandal_events")
            .select(
                "id, title, description, start_at, end_at, "
                "created_at, updated_at"
            )
            .eq("pandal_id", pandal_id)
            .order("start_at")
            .execute()
        )

        return {
            "pandal_id": pandal_id,
            "events": result.data or [],
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch events",
        )


@router.get("/events/{event_id}")
def get_event(
    event_id: UUID,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        result = (
            supabase_admin
            .table("pandal_events")
            .select(
                "id, title, description, start_at, end_at, "
                "created_at, updated_at"
            )
            .eq("id", str(event_id))
            .eq("pandal_id", pandal_id)
            .maybe_single()
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Event not found",
            )

        return {
            "event": result.data,
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch event",
        )


@router.put("/events/{event_id}")
def update_event(
    event_id: UUID,
    data: EventUpdateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        # -----------------------------------------------------
        # 1. Get existing event
        # -----------------------------------------------------

        existing = (
            supabase_admin
            .table("pandal_events")
            .select(
                "id, title, description, start_at, end_at"
            )
            .eq("id", str(event_id))
            .eq("pandal_id", pandal_id)
            .maybe_single()
            .execute()
        )

        if not existing.data:
            raise HTTPException(
                status_code=404,
                detail="Event not found",
            )

        event = existing.data

        # -----------------------------------------------------
        # 2. Keep existing values when fields aren't supplied
        # -----------------------------------------------------

        start_at = data.start_at or datetime.fromisoformat(
            event["start_at"].replace("Z", "+00:00")
        )

        end_at = data.end_at or datetime.fromisoformat(
            event["end_at"].replace("Z", "+00:00")
        )

        validate_event_times(
            start_at,
            end_at,
        )

        # -----------------------------------------------------
        # 3. Build update
        # -----------------------------------------------------

        update_data = {
            "updated_at": datetime.now(
                start_at.tzinfo
            ).isoformat(),
        }

        if data.title is not None:
            update_data["title"] = data.title

        if data.description is not None:
            update_data["description"] = data.description

        if data.start_at is not None:
            update_data["start_at"] = data.start_at.isoformat()

        if data.end_at is not None:
            update_data["end_at"] = data.end_at.isoformat()

        # -----------------------------------------------------
        # 4. Update database
        # -----------------------------------------------------

        result = (
            supabase_admin
            .table("pandal_events")
            .update(update_data)
            .eq("id", str(event_id))
            .eq("pandal_id", pandal_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update event",
            )

        # -----------------------------------------------------
        # 5. Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="UPDATE",
            entity_type="EVENT",
            entity_id=str(event_id),
            old_value=None,
            new_value=update_data,
            request=request,
        )

        return {
            "message": "Event updated successfully",
            "event": result.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        print("EVENT UPDATE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to update event",
        )


@router.delete("/events/{event_id}")
def delete_event(
    event_id: UUID,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        result = (
            supabase_admin
            .table("pandal_events")
            .delete()
            .eq("id", str(event_id))
            .eq("pandal_id", pandal_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Event not found",
            )

        # -----------------------------------------------------
        # Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="DELETE",
            entity_type="EVENT",
            entity_id=str(event_id),
            old_value=None,
            new_value=None,
            request=request,
        )

        return {
            "message": "Event deleted successfully",
            "event_id": str(event_id),
        }

    except HTTPException:
        raise

    except Exception as e:
        print("EVENT DELETE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to delete event",
        )