from database.db_connection import supabase

async def get_user_by_jwt(jwt: str):
    if not jwt:
        raise ValueError("JWT is required")
    resp = await supabase.auth.get_user(jwt)
    if not resp.user:
        raise ValueError("User not found for provided JWT")
    return resp.user
