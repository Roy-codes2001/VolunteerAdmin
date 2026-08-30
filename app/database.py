from supabase import create_client, Client

from app.config import settings


supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_secret_key,
)