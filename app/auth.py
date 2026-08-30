from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from fastapi import Depends
from app.dependencies import get_current_user

from app.database import supabase_admin


router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SignupResponse(BaseModel):
    message: str
    pandal_id: str
    email: str


@router.post("/signup", response_model=SignupResponse)
def signup(request: SignupRequest):

    try:
        # Create Supabase Auth user
        response = supabase_admin.auth.admin.create_user(
            {
                "email": request.email,
                "password": request.password,
                "email_confirm": True,
                "user_metadata": {
                    "pandal_name": request.name,
                },
            }
        )

        user = response.user

        if user is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to create authentication user",
            )

        # The Auth user's UUID is also our pandal ID
        pandal_id = str(user.id)

        # Create pandal profile
        supabase_admin.table("pandals").insert(
            {
                "id": pandal_id,
                "name": request.name,
                "contact_email": request.email,
            }
        ).execute()

        return SignupResponse(
            message="Pandal registered successfully",
            pandal_id=pandal_id,
            email=request.email,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    pandal_id: str


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):

    try:
        response = supabase_admin.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        if response.session is None or response.user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        return LoginResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            pandal_id=str(response.user.id),
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    
@router.get("/adminuser")
def get_me(current_user=Depends(get_current_user)):
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
    }