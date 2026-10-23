from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select, delete
from db.database import get_session
from db.models import Task, TimetableEvent, DailyPlan, PlanBlock

class ReplannerService:
    @staticmethod
    def replan_day(user_id=1):
        now = datetime.now(timezone.utc)
        today_str = now.strftime('%Y-%m-%d')
        with get_session() as session:
            plan = session.exec(select(DailyPlan).where(DailyPlan.plan_date == today_str)).first()
            if not plan: return None, "No plan found."
            blocks = session.exec(select(PlanBlock).where(PlanBlock.daily_plan_id == plan.id)).all()
            tasks_to_reschedule = [b for b in blocks if b.end_time < now and b.status != "done" and b.block_type == "task"]
            day_of_week = now.strftime('%a').lower()
            events = session.exec(select(TimetableEvent).where(TimetableEvent.day_of_week == day_of_week, TimetableEvent.is_fixed == True)).all()
            session.exec(delete(PlanBlock).where(PlanBlock.daily_plan_id == plan.id))
            for e in events:
                start = datetime.strptime(e.start_time, "%H:%M").time()
                end = datetime.strptime(e.end_time, "%H:%M").time()
                event_start = datetime.combine(now.date(), start).replace(tzinfo=timezone.utc)
                if event_start > now:
                    session.add(PlanBlock(daily_plan_id=plan.id, title=e.title, start_time=event_start, end_time=datetime.combine(now.date(), end).replace(tzinfo=timezone.utc), block_type="event"))
            current_slot = now
            for t in tasks_to_reschedule:
                session.add(PlanBlock(daily_plan_id=plan.id, title=t.title, task_id=t.task_id, start_time=current_slot, end_time=current_slot + timedelta(minutes=30), block_type="task"))
                current_slot += timedelta(minutes=45)
            session.commit()
            return True, "Day replanned!"
