from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    timezone: str = "UTC"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    notes: Optional[str] = None
    status: str = "todo" 
    priority: str = "medium" 
    due_at: Optional[datetime] = None
    time_estimate_minutes: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimetableEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    category: str = "other"
    start_time: str 
    end_time: str   
    day_of_week: str 
    is_fixed: bool = True

class DailyPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    plan_date: str 
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlanBlock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    daily_plan_id: int = Field(foreign_key="dailyplan.id")
    title: str
    start_time: datetime
    end_time: datetime
    block_type: str 
    status: str = "planned"
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")

class Note(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str = "Untitled"
    content: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Habit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    frequency: str = "daily"
    current_streak: int = 0
    longest_streak: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HabitLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key="habit.id")
    date: str 
    status: str = "done"
