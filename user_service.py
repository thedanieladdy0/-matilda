from sqlmodel import Session, select
from db.database import get_session
from db.models import User

class UserService:
    @staticmethod
    def create_user(name: str):
        with get_session() as session:
            user = User(name=name)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    @staticmethod
    def get_user_by_id(user_id: int):
        with get_session() as session:
            return session.get(User, user_id)

    @staticmethod
    def get_all_users():
        with get_session() as session:
            return session.exec(select(User)).all()
