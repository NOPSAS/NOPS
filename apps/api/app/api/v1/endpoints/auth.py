"""
ByggSjekk – Authentication endpoints.

POST /auth/register  – create a new user account
POST /auth/login     – exchange credentials for a JWT
GET  /auth/me        – return the current authenticated user
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserRead, UserUpdate
from app.services.email import generer_token, send_verifisering, send_passord_reset, send_velkomst
from app.core.config import get_settings

router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and receive an access token",
)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    # Check for existing account
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="En konto med denne e-postadressen finnes allerede.",
        )

    user = User(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
        is_architect=body.is_architect,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Send e-postbekreftelse
    settings = get_settings()
    if settings.SMTP_USER:
        token = generer_token()
        user.email_verification_token = token
        await db.flush()
        import asyncio
        asyncio.create_task(send_verifisering(
            til=user.email,
            navn=user.full_name or user.email,
            token=token,
            base_url=settings.NOPS_BASE_URL,
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_user=settings.SMTP_USER,
            smtp_password=settings.SMTP_PASSWORD,
        ))

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.post(
    "/login",
    response_model=Token,
    summary="Obtain a JWT access token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == form_data.username))
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/verify-email", summary="Bekreft e-postadresse")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.email_verification_token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Ugyldig eller utløpt bekreftelseslenke")
    user.email_verified = True
    user.email_verification_token = None
    await db.flush()
    settings = get_settings()
    if settings.SMTP_USER:
        import asyncio
        asyncio.create_task(send_velkomst(
            til=user.email,
            navn=user.full_name or user.email,
            base_url=settings.NOPS_BASE_URL,
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_user=settings.SMTP_USER,
            smtp_password=settings.SMTP_PASSWORD,
        ))
    return {"message": "E-postadresse bekreftet. Velkommen til nops.no!"}


@router.post("/forgot-password", summary="Be om passordtilbakestilling")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        settings = get_settings()
        token = generer_token()
        user.password_reset_token = token
        await db.flush()
        if settings.SMTP_USER:
            import asyncio
            asyncio.create_task(send_passord_reset(
                til=user.email,
                navn=user.full_name or user.email,
                token=token,
                base_url=settings.NOPS_BASE_URL,
                smtp_host=settings.SMTP_HOST,
                smtp_port=settings.SMTP_PORT,
                smtp_user=settings.SMTP_USER,
                smtp_password=settings.SMTP_PASSWORD,
            ))
    # Alltid returner samme svar (sikkerhet)
    return {"message": "Hvis e-postadressen finnes, har vi sendt instruksjoner for tilbakestilling."}


@router.post("/reset-password", summary="Tilbakestill passord med token")
async def reset_password(token: str, new_password: str, db: AsyncSession = Depends(get_db)) -> dict:
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Passordet må være minst 8 tegn")
    result = await db.execute(select(User).where(User.password_reset_token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Ugyldig eller utløpt tilbakestillingslenke")
    from app.core.security import get_password_hash
    user.hashed_password = get_password_hash(new_password)
    user.password_reset_token = None
    await db.flush()
    return {"message": "Passordet er oppdatert. Du kan nå logge inn."}


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user profile",
)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.password is not None:
        current_user.hashed_password = get_password_hash(body.password)
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return current_user
