from datetime import datetime
from sqlmodel import select
from db.database import get_session
from db.models import Task, HabitLog
from ai.client import MatildaAI
from ai.prompts import REVIEW_PROMPT

class ReviewService:
    @staticmethod
    def generate_daily_review(user_id=1):
        today_str = datetime.now().strftime('%Y-%m-%d')
        with get_//session() as session:
            done = session.exec(select(Task).where(Task.user_id == user_id, Task.status == "done")).all()
            pending = session.exec(select(Task).where(Task.user_id == user_id, Task.status == "todo")).all()
            habits = session.exec(select(HabitLog).where(HabitLog.date == today_str, HabitLog.status == "done")).all()
            prompt = f"Done: {[t.title for t in done]}, Pending: {[t.title for t in pending]}, Habits: {len(habits)}"
            return MatildaAI().generate_response(prompt=prompt, system_prompt=REVIEW_PROMPT)
