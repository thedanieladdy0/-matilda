from sqlmodel import Session, select
from db.database import get_session
from db.models import TimetableEvent

class TimetableService:
    @staticmethod
    def create_event(title: str, category: str, start_time: str, end_time: str, day_of_week: str, is_fixed: bool = True):
        with get_session() as session:
            new_event = TimetableEvent(
                title=title,
                category=category,
                start_time=start_time,
                end_time=end_time,
                day_of_week=day_of_week,
                is_fixed=is_fixed,
                user_id=1 # Default user
            )
            session.add(new_event)
            session.commit()
            session.refresh(new_event)
            return new_event

    @staticmethod
    def get_events_for_day(day_of_week: str):
        with get_session() as session:
            statement = select(TimetableEvent).where(TimetableEvent.day_of_week == day_of_week)
            return session.exec(statement).all()

    @staticmethod
    def get_all_events():
        with get_session() as session:
            return session.exec(select(TimetableEvent)).all()

    @staticmethod
    def delete_event(event_id: int):
        with get_session() as session:
            event = session.get(TimetableEvent, event_id)
            if event:
                session.delete(event)
                session.commit()
                return True
            return False
from sqlmodel import Session, select
from db.database import get_session
from db.models import TimetableEvent

class TimetableService:
    @staticmethod
    def create_event(title, category, start_time, end_time, day_of_week, is_fixed=True):
        with get_session() as session:
            event = TimetableEvent(title=title, category=category, start_time=start_time, end_time=end_time, day_of_week=day_of_week, is_fixed=is_fixed, user_id=1)
            session.add(event)
            session.commit()
            return event

    @staticmethod
    def get_all_events():
        with get_session() as session:
            return session.exec(select(TimetableEvent)).all()

    @staticmethod
    def delete_event(event_id):
        with get_//session() as session:
            event = session.get(TimetableEvent, event_id)
            if event:
                session.delete(event)
                session.commit()
