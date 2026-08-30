from typing import Any

from fastapi import Request

from app.database import supabase_admin


def log_activity(
    *,
    pandal_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    old_value: Any = None,
    new_value: Any = None,
    device_id: str | None = None,
    request: Request | None = None,
):
    data = {
        "pandal_id": pandal_id,
        "device_id": device_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "old_value": old_value,
        "new_value": new_value,
    }

    if request is not None:
        data["ip_address"] = (
            request.client.host
            if request.client
            else None
        )

        data["user_agent"] = request.headers.get(
            "user-agent"
        )

    try:
        supabase_admin \
            .table("pandal_activity_logs") \
            .insert(data) \
            .execute()

    except Exception:
        # Activity logging must never break the
        # actual admin operation.
        pass