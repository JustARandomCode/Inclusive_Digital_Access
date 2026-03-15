from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import LoginRequest, TokenResponse, RegisterRequest, UserInDB
from config import settings
from database import get_database
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    exc = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        username: str | None = payload.get("sub")
        if not username:
            raise exc
        return username
    except JWTError:
        raise exc


@router.post("/register", status_code=201)
async def register(request: RegisterRequest):
    """
    Create a new user account. In production, restrict this endpoint
    to admin roles or remove it and provision users out-of-band.
    """
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(request.password) > 72:
        raise HTTPException(status_code=400, detail="Password must be 72 characters or fewer")

    db = get_database()
    existing = await db.users.find_one({"username": request.username})
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = UserInDB(
        username=request.username,
        hashed_password=hash_password(request.password),
    )
    await db.users.insert_one(user.model_dump())
    logger.info(f"Registered new user: {request.username}")
    return {"message": "User created"}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    db = get_database()
    user_doc = await db.users.find_one({"username": request.username})

    # Constant-time path: always verify even if user not found to prevent timing attacks
    dummy_hash = "$2b$12$KIXeOjFlmkOCk3HEGKFk8.invalid.hash.for.timing"
    stored_hash = user_doc["hashed_password"] if user_doc else dummy_hash

    if not user_doc or not verify_password(request.password, stored_hash):
        logger.warning(f"Failed login for: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": request.username})
    logger.info(f"Login successful: {request.username}")
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/verify")
async def verify(username: str = Depends(verify_token)):
    return {"username": username, "status": "authenticated"}
