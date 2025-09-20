import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.deps import get_db
from domains.waitlist.services.waitlist_service import WaitlistService

router = APIRouter()


class WaitlistCreate(BaseModel):
    email: EmailStr


class WaitlistResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr

    class Config:
        from_attributes = True


@router.post(
    "/waitlist",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join the waitlist",
    tags=["waitlist"],
)
def join_waitlist(
    payload: WaitlistCreate, db: Session = Depends(get_db)
) -> "WaitlistResponse":
    """
    Add a user's email to the waitlist.

    This public endpoint allows a user to submit their email address to be added
    to the platform's waitlist. The service ensures that emails are unique.

    - **email**: The user's email address.

    If the email already exists, it returns a 409 Conflict error.
    """
    waitlist_service = WaitlistService(db)
    try:
        waitlist_entry = waitlist_service.add_to_waitlist_by_email(payload.email)
        return WaitlistResponse.from_orm(waitlist_entry)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists on the waitlist.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
