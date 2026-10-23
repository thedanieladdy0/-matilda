from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from db.database import get_session
from db.models import Task, TimetableEvent, DailyPlan, PlanBlock

class PlannerService:
    @staticmethod
    def generate_daily_plan(user_id=1):
        now = datetime.now(timezone.utc)
        today_str = now.strftime('%Y-%m-%d')
        day_of_week = now.strftime('%a').lower()
        with get_//session() as session:
            events = session.exec(select(TimetableEvent).where(TimetableEvent.day_of_week == day_of_week)).all()
            tasks = session.exec(select(Task).where(Task.user_id == user_id, Task.status == "todo")).all()
            plan = DailyPlan(user_id=user_id, plan_date=today_str)
            session.add(plan)
            session.commit()
            session.refresh(plan)
            current_time = datetime.combine(now.date(), datetime.strptime("08:00", "%H:%M").time()).replace(tzinfo=timezone.utc)
            for e in events:
                start = datetime.strptime(e.start_time, "%H:%M").time()
                end = datetime.strptime(e.end_time, "%H:%M").time()
                session.add(PlanBlock(daily_plan_id=plan.id, title=e.title, start_time=datetime.combine(now.date(), start).replace(tzinfo=timezone.utc), end_time=datetime.combine(now.date(), end).replace(tzinfo=timezone.utc), block_type="event"))
            for t in tasks:
                duration = t.time_estimate_minutes or 30
                session.add(PlanBlock(daily_plan_id=plan.id, title=t.title, task_id=t.id, start_time=current_time, end_time=current_time + timedelta(minutes=duration), block_type="task"))
                current_time += timedelta(minutes=duration + 15)
            session.commit()
            return plan.id
