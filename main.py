import streamlit as st
import json
import re
import time
import dateparser
from datetime import datetime, timezone, timedelta
from sqlmodel import select
from db.database import init_db, get_session
from db.models import Note, PlanBlock, DailyPlan
from ai.client import MatildaAI
from ai.prompts import TASK_EXTRACTION_PROMPT, AGENT_PROMPT
from services.task_service import TaskService
from services.timetable_service import TimetableService
from services.note_service import NoteService
from services.planner_service import PlannerService
from services.replanner_service import ReplannerService
from services.habit_service import HabitService
from services.review_service import ReviewService
from services.agent_service import AgentService

# 1. Page Config
st.set_page_config(page_title="matilda", page_icon="🌸", layout="wide")
init_db()

# Professional Typography and Glassmorphism CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Barriecito&family=Belleza:wght@400;700&display=swap');
    
    /* Apply Inter font to the main app body only, not internal Streamlit components */
    .stApp { 
        background-color: #FDFBF7; 
        font-family: 'Inter', sans-serif !important; 
    }
    
    /* target only the actual text content to avoid breaking icons/expanders */
    p, div, span, label { 
        font-family: 'Inter', sans-serif; 
    }

    /* Professional Headers */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
        font-family: 'Barriecito', cursive !important; 
        color: #2C3E50; 
    }
    
    [data-testid="stSidebar"] { background-color: #F5F2ED; }
    
    .timeline-block {
        padding: 20px;
        border-radius: 15px;
        border-left: 6px solid #BDBDBD;
        background-color: white;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .status-pill { background-color: #E8F5E9; color: #2E7D32; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .deadline-text { color: #D32F2F; font-weight: bold; font-size: 14px; }
    .stButton>button { border-radius: 20px; border: 1px solid #DDD; }
    </style>
""", unsafe_allow_html=True)

def show_ai_status():
    try:
        ai = MatildaAI()
        if ai.check_connection(): st.sidebar.success("AI: Local Model Ready")
        else: st.sidebar.error("AI: Ollama Not Found")
    except: st.sidebar.error("AI: Connection Error")

def extract_json(text):
    try:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match: return match.group(1)
    except: pass
    return text

def get_time_remaining(due_date):
    if not due_date: return None
    now = datetime.now(timezone.utc)
    diff = due_date - now 
    if diff.total_seconds() < 0: return "Overdue! 🚨"
    days, hours, minutes = diff.days, diff.seconds // 3600, (diff.seconds // 60) % 60
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    return "⏳ " + ", ".join(parts) if parts else "⏳ Due soon"

# Sidebar
st.sidebar.title("🌸 matilda")
st.sidebar.markdown('<span class="status-pill">Private · Offline</span>', unsafe_allow_html=True)
show_ai_status()

menu = st.sidebar.radio("Navigate", ["Chat", "Today", "Timetable", "Tasks", "Habits", "Notes", "Review", "Settings"])

# --- QUICK ADD LOGIC ---
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Quick Add")
if 'quick_input' not in st.session_state:
    st.session_state['quick_input'] = ""

PREDICTIONS = ["tomorrow", "this Friday", "for 30 mins", "for 1 hour", "priority high", "priority medium"]
st.sidebar.write("✨ Suggestions:")
cols = st.sidebar.columns(2)
for i, sug in enumerate(PREDICTIONS):
    with cols[i % 2]:
        if st.button(sug, key=f"sug_{i}"):
            st.session_state['quick_input'] += f" {sug}"
            st.rerun()

user_input = st.sidebar.text_input("What's on your mind?", value=st.session_state['quick_input'])
if user_input != st.session_state['quick_input']:
    st.session_state['quick_input'] = user_input

if st.sidebar.button("Add Task", type="primary"):
    if user_input:
        with st.spinner("matilda is thinking..."):
            ai = MatildaAI()
            response = ai.generate_response(prompt=user_input, system_prompt=TASK_EXTRACTION_PROMPT)
            try:
                cleaned_json = extract_json(response)
                data = json.loads(cleaned_json)
                if 'tasks' in data:
                    for t in data['tasks']:
                        due_date = None
                        raw_date_desc = t.get('due_at')
                        if raw_date_desc:
                            parsed = dateparser.parse(raw_date_desc, settings={'RELATIVE_BASE': datetime.now(), 'PREFER_DATES_FROM': 'future'})
                            if parsed: due_date = parsed.replace(tzinfo=timezone.utc)
                        TaskService.create_task(
                            title=t.get('title', user_input), 
                            priority=t.get('priority', 'medium'), 
                            due_at=due_date, 
                            estimate=t.get('estimated_minutes')
                        )
                    st.success("✅ Task added!")
                    st.session_state['quick_input'] = ""
                    st.rerun()
                else:
                    TaskService.create_task(title=user_input)
            except:
                TaskService.create_task(title=user_input)
                st.warning("Added as simple task.")

# --- PAGE ROUTING ---
if menu == "Chat":
    st.title("Chat with matilda 💬")
    
    # 1. Initialize messages globally in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 2. Display chat history from session state
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Handle new user input
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent = AgentService()
                
                # FIXED: Pass the entire history to the agent, not just the prompt
                # This allows matilda to "remember" previous messages
                response = agent.handle_message(
                    prompt=prompt, 
                    history=st.session_state.messages
                )
                st.markdown(response)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # We use st.rerun() only if necessary, but for chat_input it's usually automatic


elif menu == "Today":
    st.title("Good morning, Ama ☀️")
    col_welcome, col_action = st.columns([0.6, 0.4])
    with col_welcome:
        st.markdown("### Your Day at a Glance")
        st.write("Matilda combines your fixed schedule and tasks into one doable plan.")
    with col_action:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🪄 Plan My Day", use_container_width=True):
                with st.spinner("Calculating..."):
                    PlannerService.generate_daily_plan()
                    st.success("Plan generated!")
                    st.rerun()
        with btn_col2:
            if st.button("🔄 I'm Behind", use_container_width=True, type="primary"):
                with st.spinner("Replanning..."):
                    success, msg = ReplannerService.replan_day()
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("---")
    with get_session() as session:
        today_str = datetime.now().strftime('%Y-%m-%d')
        plan = session.exec(select(DailyPlan).where(DailyPlan.plan_date == today_str)).first()
        if plan:
            blocks = session.exec(select(PlanBlock).where(PlanBlock.daily_plan_id == plan.id)).all()
            blocks = sorted(blocks, key=lambda x: x.start_time)
            for b in blocks:
                with st.container():
                    color = "#BDBDBD"
                    if b.block_type == "event": color = "#BBDEFB"
                    elif b.block_type == "task": color = "#C8E6C9"
                    st.markdown(f"""
                        <div class="timeline-block" style="border-left-color: {color};">
                            <strong>{b.start_time.strftime('%H:%M')} - {b.end_time.strftime('%H:%M')}</strong><br>
                            {b.title} <small>({b.block_type})</small>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No plan generated for today yet. Click 'Plan My Day' to start!")

elif menu == "Timetable":
    st.title("Weekly Timetable 📅")
    
    st.markdown("### ➕ Add New Event")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            # We keep the keys exactly as they were
            st.text_input("Event Title", key="tt_title")
            st.selectbox("Category", ["Class", "Work", "Personal", "Gym", "Other"], key="tt_cat")
            st.selectbox("Day of Week", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"], key="tt_day")
        with col2:
            st.text_input("Start Time (e.g. 09:00)", key="tt_start")
            st.text_input("End Time (e.g. 10:30)", key="tt_end")
            st.checkbox("Fixed Commitment?", value=True, key="tt_fixed")
        
        if st.button("Save to Timetable", type="primary"):
            # FIXED: Check st.session_state instead of local variables
            # This ensures we get the actual text currently in the boxes
            title = st.session_state.get("tt_title", "")
            start_t = st.session_state.get("tt_start", "")
            end_t = st.session_state.get("tt_end", "")
            category = st.session_state.get("tt_cat", "Other")
            day = st.session_state.get("tt_day", "mon")
            fixed = st.session_state.get("tt_fixed", True)

            if title and start_t and end_t:
                TimetableService.create_event(title, category, start_t, end_t, day, fixed)
                st.success(f"Added {title} to your {day} schedule!")
                st.rerun()
            else:
                st.error("Please fill in the title, start time, and end time.")

    st.markdown("---")
    st.markdown("### Your Weekly Schedule")
    all_events = TimetableService.get_all_events()
    if not all_events:
        st.write("No events added yet.")
    else:
        days_order = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        for d in days_order:
            day_events = [e for e in all_events if e.day_of_week == d]
            if day_events:
                with st.expander(f"📅 {d.upper()}", expanded=False):
                    for e in day_events:
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1: 
                            st.write(f"**{e.start_time} - {e.end_time}** | {e.title} ({e.category})")
                        with col2:
                            if st.button("🗑️", key=f"del_tt_{e.id}"):
                                TimetableService.delete_event(e.id)
                                st.rerun()

elif menu == "Tasks":
    st.title("Your Tasks 📝")
    tasks = TaskService.get_all_tasks()
    if not tasks:
        st.write("No tasks yet!")
    else:
        for task in tasks:
            with st.container():
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                with col1:
                    st.markdown(f"### {task.title}")
                    details = []
                    if task.priority: details.append(f"🚩 {task.priority}")
                    if task.due_at: details.append(f"📅 {task.due_at.strftime('%Y-%m-%d')}")
                    if task.time_estimate_minutes: details.append(f"⏳ {task.time_estimate_minutes} mins")
                    st.write(" | ".join(details) if details else "⚪ No details")
                    time_left = get_time_remaining(task.due_at)
                    if time_left:
                        st.markdown(f"<span class='deadline-text'>{time_left} remaining until deadline</span>", unsafe_allow_html=True)
                with col2:
                    if task.time_estimate_minutes:
                        if st.button(f"Start ⏳", key=f"start_{task.id}"):
                            st.session_state[f"timer_{task.id}"] = task.time_estimate_minutes * 60
                            st.rerun()
                    if f"timer_{task.id}" in st.session_state:
                        placeholder = st.empty()
                        while st.session_state[f"timer_{task.id}"] > 0:
                            mins, secs = divmod(st.session_state[f"timer_{task.id}"], 60)
                            placeholder.markdown(f"⏱️ **{mins:02d}:{secs:02d}**")
                            time.sleep(1)
                            st.session_state[f"timer_{task.id}"] -= 1
                            st.rerun() 
                with col3:
                    if st.button("Done ✅", key=f"done_{task.id}"):
                        TaskService.mark_complete(task.id)
                        st.rerun()
                st.markdown("---")

elif menu == "Habits":
    st.title("Habit Tracker 📈")
    st.markdown("#### ➕ Add New Habit")
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        h_title = st.text_input("Habit Name (e.g. Read 10 pages)", key="habit_name")
        h_freq = st.selectbox("Frequency", ["daily", "weekdays", "weekly"], key="habit_freq")
    with col2:
        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
        if st.button("Save Habit", use_container_width=True):
            if h_title:
                HabitService.create_habit(h_title, h_freq)
                st.success("Habit added!")
                st.rerun()
            else:
                st.error("Please enter a habit name.")

    st.markdown("---")
    st.markdown("### My Habits")
    habits = HabitService.get_all_habits()
    if not habits:
        st.write("No habits yet. Start building some streaks!")
    else:
        for h in habits:
            with st.container():
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                with col1:
                    st.markdown(f"### {h.title}")
                    st.write(f"Frequency: {h.frequency}")
                with col2:
                    st.metric("Current Streak", f"{h.current_streak} days")
                with col3:
                    if st.button(f"Check-in ✅", key=f"habit_{h.id}"):
                        if HabitService.log_habit(h.id):
                            st.success("Streak increased!")
                            st.rerun()

elif menu == "Notes":
    st.title("Private Notes ✍️")
    if 'active_note_id' not in st.session_state:
        st.session_state['active_note_id'] = None
        
    col_list, col_edit = st.columns([1, 3])
    
    with col_list:
        st.subheader("My Notes")
        if st.button("➕ New Note", use_container_width=True):
            new_note = NoteService.create_note("Untitled", "")
            st.session_state['active_note_id'] = new_note.id
            st.rerun()
            
        st.markdown("---")
        notes = NoteService.get_all_notes()
        if not notes:
            st.info("No notes yet. Create one!")
        else:
            for n in notes:
                is_active = (st.session_state['active_note_id'] == n.id)
                label = f"📌 {n.title}" if is_active else f"📄 {n.title}"
                if st.button(label, key=f"sel_note_{n.id}", use_container_width=True):
                    st.session_state['active_note_id'] = n.id
                    st.rerun()

    with col_edit:
        if st.session_state['active_note_id']:
            with get_session() as session:
                active_note = session.get(Note, st.session_state['active_note_id'])
            
            if active_note:
                new_title = st.text_input("Title", value=active_note.title, label_visibility="collapsed", key="note_title_input")
                new_content = st.text_area("Content", value=active_note.content, height=500, label_visibility="collapsed", key="note_content_input")
                
                col_save, col_del = st.columns([1, 1])
                with col_save:
                    if st.button("Save Changes", type="primary", use_container_width=True):
                        NoteService.update_note(active_note.id, new_title, new_content)
                        st.success("Saved!")
                        st.rerun()
                with col_del:
                    if st.button("Delete Note", use_container_width=True):
                        NoteService.delete_note(active_note.id)
                        st.session_state['active_note_id'] = None
                        st.rerun()
        else:
            st.info("👈 Select a note from the list or create a new one to start writing.")

elif menu == "Review":
    st.title("Daily Reflection 🌙")
    if st.button("Generate My Review", use_container_width=True):
        with st.spinner("Reflecting..."):
            review = ReviewService.generate_daily_review()
            st.markdown(f"### Matilda's Thoughts:\n\n {review}")
            st.balloons()

elif menu == "Settings":
    st.title("Settings")
    st.text_input("Your Name", value="Ama")
