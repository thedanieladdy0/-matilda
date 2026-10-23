from datetime import datetime
from sqlmodel import Session, select
from db.database import get_session
from db.models import Habit, HabitLog

class HabitService:
    @staticmethod
    def create_habit(title: str, frequency: str = "daily", user_id: int = 1):
        with get_//session() as session:
            habit = Habit(title=title, frequency=frequency, user_id=user_id)
            session.add(habit)
            session.commit()
            session.refresh(habit)
            return habit

    @staticmethod
    def get_all_habits(user_id: int = 1):
        with get_session() as session:
            return session.exec(select(Habit).where(Habit.user_id == user_id)).all()

    @staticmethod
    def log_habit(habit_id: int, status: str = "done"):
        today = datetime.now().strftime('%Y-%m-%d')
        with get_session() as session:
            existing = session.exec(select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.date == today)).first()
            if existing: return False
            log = HabitLog(habit_id=habit_id, date=today, status=status)
            session.add(log)
            habit = session.get(Habit, habit_id)
            if habit:
                if status == "done":
                    habit.current_streak += 1
                    if habit.current_streak > habit.longest_streak:
                        habit.longest_streak = habit.current_streak
                else:
                    habit.current_streak = 0
                session.add(habit)
            session.commit()
            return True
