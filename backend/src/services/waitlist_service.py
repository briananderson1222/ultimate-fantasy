from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Waitlist


class WaitlistService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_to_waitlist(self, email: str) -> Waitlist:
        """Adds a new email to the waitlist.

        Args:
            email: The email address to add.

        Returns:
            The created Waitlist object.

        Raises:
            IntegrityError: If the email already exists.
        """
        try:
            waitlist_entry = Waitlist(email=email)
            self.db.add(waitlist_entry)
            self.db.commit()
            self.db.refresh(waitlist_entry)
            return waitlist_entry
        except IntegrityError:
            self.db.rollback()
            raise
