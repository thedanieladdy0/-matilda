from sqlmodel import Session, select
from db.database import get_session
from db.models import Task

class TaskService:
    @staticmethod
    def create_task(title: str, user_id: int = 1, priority="medium", due_at=None, estimate=None):
        with get_session() as session:
            task = Task(title=title, user_id=user_id, priority=priority, due_at=due_at, time_estimate_minutes=estimate)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    @staticmethod
    def get_all_tasks(user_id: int = 1):
        with get_session() as session:
            return session.exec(select(Task).where(Task.user_id == user_id)).all()

    @staticmethod
    def mark_complete(task_id: int):
        with get_session() as session:
            task = session.get(Task, task_id)
            if task:
                task.status = "done"
                session.add(task)
                session.commit()
