from typing import List, Optional

from bot.db import Session
from bot.models import User


def add_or_update_user(user_id: int, username: Optional[str], full_name: str) -> None:
    with Session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.username = username
            user.full_name = full_name
            user.usage_count += 1
        else:
            user = User(user_id=user_id, username=username, full_name=full_name, usage_count=1)
            session.add(user)
        session.commit()


def get_all_users() -> List[User]:
    with Session() as session:
        return session.query(User).all()
