from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.activity_log import log_activity
from app.database import supabase_admin
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Photos"],
)


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/photos")
async def upload_photo(
    file: UploadFile = File(...),
    request: Request = None,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    # ---------------------------------------------------------
    # 1. Validate file type
    # ---------------------------------------------------------

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WEBP images are allowed",
        )

    # ---------------------------------------------------------
    # 2. Read file and validate size
    # ---------------------------------------------------------

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image size must not exceed 20 MB",
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    try:
        # -----------------------------------------------------
        # 3. Find next available display order
        # -----------------------------------------------------

        existing = (
            supabase_admin
            .table("pandal_photos")
            .select("display_order")
            .eq("pandal_id", pandal_id)
            .order("display_order")
            .execute()
        )

        used_orders = {
            row["display_order"]
            for row in (existing.data or [])
        }

        display_order = next(
            (
                order
                for order in range(1, 6)
                if order not in used_orders
            ),
            None,
        )

        if display_order is None:
            raise HTTPException(
                status_code=400,
                detail="A pandal can have a maximum of 5 photos",
            )

        # -----------------------------------------------------
        # 4. Generate server-side storage path
        # -----------------------------------------------------

        photo_id = uuid4()

        extension = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }[file.content_type]

        storage_path = f"{pandal_id}/{photo_id}.{extension}"

        # -----------------------------------------------------
        # 5. Upload to Supabase Storage
        # -----------------------------------------------------

        supabase_admin.storage.from_("pandal-photos").upload(
            storage_path,
            file_bytes,
            {
                "content-type": file.content_type,
                "upsert": False,
            },
        )

        # -----------------------------------------------------
        # 6. Store metadata in PostgreSQL
        # -----------------------------------------------------

        result = (
            supabase_admin
            .table("pandal_photos")
            .insert(
                {
                    "id": str(photo_id),
                    "pandal_id": pandal_id,
                    "storage_path": storage_path,
                    "display_order": display_order,
                }
            )
            .execute()
        )

        if not result.data:
            supabase_admin.storage.from_("pandal-photos").remove(
                [storage_path]
            )

            raise HTTPException(
                status_code=500,
                detail="Failed to save photo metadata",
            )

        # -----------------------------------------------------
        # 7. Get public URL
        # -----------------------------------------------------

        public_url = (
            supabase_admin
            .storage
            .from_("pandal-photos")
            .get_public_url(storage_path)
        )

        # -----------------------------------------------------
        # 8. Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="CREATE",
            entity_type="PHOTO",
            entity_id=str(photo_id),
            old_value=None,
            new_value={
                "display_order": display_order,
                "storage_path": storage_path,
                "content_type": file.content_type,
            },
            request=request,
        )

        return {
            "message": "Photo uploaded successfully",
            "photo": {
                "id": str(photo_id),
                "pandal_id": pandal_id,
                "display_order": display_order,
                "storage_path": storage_path,
                "url": public_url,
            },
        }

    except HTTPException:
        raise

    except Exception as e:
        print("PHOTO UPLOAD ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to upload photo",
        )


@router.get("/photos")
def get_photos(
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        result = (
            supabase_admin
            .table("pandal_photos")
            .select("id, display_order, storage_path, created_at")
            .eq("pandal_id", pandal_id)
            .order("display_order")
            .execute()
        )

        photos = []

        for photo in result.data or []:
            public_url = (
                supabase_admin
                .storage
                .from_("pandal-photos")
                .get_public_url(photo["storage_path"])
            )

            photos.append(
                {
                    "id": photo["id"],
                    "display_order": photo["display_order"],
                    "url": public_url,
                    "created_at": photo["created_at"],
                }
            )

        return {
            "pandal_id": pandal_id,
            "photos": photos,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch photos",
        )
    
    # except Exception as e:
    #     print("PHOTO UPLOAD ERROR:", repr(e))

    #     raise HTTPException(
    #         status_code=500,
    #         detail=str(e),
    #     )


@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    pandal_id = str(current_user.id)

    try:
        # -----------------------------------------------------
        # 1. Find the photo belonging to this pandal
        # -----------------------------------------------------

        result = (
            supabase_admin
            .table("pandal_photos")
            .select("id, storage_path, display_order")
            .eq("id", photo_id)
            .eq("pandal_id", pandal_id)
            .maybe_single()
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Photo not found",
            )

        photo = result.data
        storage_path = photo["storage_path"]

        # -----------------------------------------------------
        # 2. Delete file from Storage
        # -----------------------------------------------------

        supabase_admin.storage.from_("pandal-photos").remove(
            [storage_path]
        )

        # -----------------------------------------------------
        # 3. Delete database record
        # -----------------------------------------------------

        delete_result = (
            supabase_admin
            .table("pandal_photos")
            .delete()
            .eq("id", photo_id)
            .eq("pandal_id", pandal_id)
            .execute()
        )

        if not delete_result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete photo metadata",
            )

        # -----------------------------------------------------
        # 4. Activity log
        # -----------------------------------------------------

        log_activity(
            pandal_id=pandal_id,
            action="DELETE",
            entity_type="PHOTO",
            entity_id=photo_id,
            old_value=None,
            new_value=None,
            request=request,
        )

        return {
            "message": "Photo deleted successfully",
            "photo_id": photo_id,
        }

    except HTTPException:
        raise

    except Exception as e:
        print("PHOTO DELETE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to delete photo",
        )