import os
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from fastapi import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin.auth import ExpiredIdTokenError
from firebase_admin import auth
from mosayic.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

AVATAR_PLACEHOLDER_URL = os.getenv("AVATAR_PLACEHOLDER_URL", "")
ADMIN_ROLE = 'admin'

class FirestoreUser(BaseModel):
    """
    This will be the structure of the user object stored in firestore.
    """
    uid: str
    email: str = 'noaddress@email.com'
    display_name: str = 'Unnamed'
    photo_url: str = AVATAR_PLACEHOLDER_URL
    is_admin: bool = False


class FirebaseUser(BaseModel):
    """
    When a firebase auth token is validated and decoded, this
    is the structure of the user data returned.
    """
    uid: str
    email_verified: bool = False
    email: str = 'noaddress@email.com'
    picture: str = AVATAR_PLACEHOLDER_URL
    name: str = 'Guest'
    auth_time: int
    iat: int
    exp: int
    role: str = "user"


class FirebaseAuthUser(BaseModel):
    """
    The user structure from the firebase auth Python SDK differs slightly from
    FirebaseUser, so this model is used to represent that user object.
    """
    uid: str
    email: str = 'noaddress@email.com'
    display_name: str | None = None
    photo_url: str | None = None
    last_login_at: str
    created_at: str
    custom_attributes: str | None = None


class FirebaseUserClaims(BaseModel):
    """
    Some tokens have custom claims, and this feature is used by mosayic
    to assign and manage admin rights at the token level.
    """
    uid: str
    role: str = 'admin'


async def get_admin_user(token: HTTPAuthorizationCredentials = Depends(security)) -> FirebaseUser:
    """Verify the JWT token, check for the admin service role, and then return the user object."""
    current_user = await get_current_user(token)
    if current_user.role == ADMIN_ROLE:
        return current_user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not an admin.")


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security), require_verified_email: bool = False) -> FirebaseUser:
    """Verify the JWT token and return the user object."""
    try:
        decoded_token = auth.verify_id_token(token.credentials)
        if require_verified_email and not decoded_token.get("email_verified"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")
        user = FirebaseUser(**decoded_token)
        return user
    except ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth token has expired")
    except Exception as e:
        logger.error("Error encountered during JWT token verification: %s", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def generate_firebase_verify_link(email: str) -> str:
    return auth.generate_email_verification_link(email)
