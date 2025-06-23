from supabase import AsyncClient
from services.env import get_env_var

url: str = get_env_var("SUPABASE_URL", "")
key: str = get_env_var("SUPABASE_KEY", "")

supabase: AsyncClient = AsyncClient(url, key)
