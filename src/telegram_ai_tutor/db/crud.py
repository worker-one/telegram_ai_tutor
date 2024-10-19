import logging
from typing import Optional
from sqlalchemy.orm import Session

from .database import get_session
from .models import User, Feedback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user(user_id: int) -> Optional[User]:
    db: Session = get_session()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()

def upsert_user(user_id: int, username: str, last_chat_id: int = None):
    db: Session = get_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.username = username
            user.last_chat_id = last_chat_id
            logger.info(f"User with id {user_id} updated successfully.")
        else:
            new_user = User(
                id=user_id,
                name=username,
                last_chat_id=last_chat_id,
            )
            db.add(new_user)
            logger.info(f"User with id {user_id} added successfully.")
        db.commit()
    finally:
        db.close()

def get_last_chat_id(user_id: int) -> Optional[int]:
    db: Session = get_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user.last_chat_id
        else:
            logger.error(f"User with id {user_id} not found in the database.")
            return None
    finally:
        db.close()

def save_feedback(user_id: int, rating: int, feedback_text: Optional[str] = None):
    db: Session = get_session()
    try:
        feedback = Feedback(
            user_id=user_id,
            rating=rating,
            feedback_text=feedback_text
        )
        db.add(feedback)
        db.commit()
        logger.info(f"Feedback from user {user_id} saved successfully.")
    finally:
        db.close()
