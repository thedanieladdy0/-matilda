# 🌸 matilda

**matilda** is a mindful, local-first AI companion designed to help you organize your life, manage your time, and reflect on your growth. Unlike traditional productivity apps, matilda combines a fixed weekly timetable with a dynamic task list to generate a realistic, doable daily plan.

![matilda Banner](https://via.placeholder.com/800x400?text=matilda+🌸+AI+Companion) <!-- Replace this with a screenshot of your app later! -->

## ✨ Key Features

- **💬 AI Chat Agent:** A conversational interface that can add tasks, reorganize your day, or just chat with you about your goals.
- **🪄 Mindful Planning:** The "Plan My Day" feature analyzes your fixed commitments and tasks to create a balanced schedule.
- **📅 Weekly Timetable:** Manage your recurring events (classes, gym, work) with ease.
- **📝 Private Notes:** A simple, clean space for your thoughts and ideas.
- **📈 Habit Tracker:** Build consistency and track your streaks.
- **🌙 Daily Review:** An AI-powered reflection tool to help you wrap up your day mindfully.
- **🔒 Local-First & Private:** Your data stays on your machine. No cloud, no tracking.

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Database:** [SQLModel](https://sqlmodel.tiangolo.com/) (SQLite)
- **AI Engine:** [Ollama](https://ollama.com/) (Local LLM)
- **Date Parsing:** [dateparser](https://dateparser.readthedocs.io/)

## 🚀 Getting Started

### Prerequisites
1. **Install Python 3.9+**
2. **Install Ollama:** Download it from [ollama.com](https://ollama.com/).
3. **Pull the Model:** Run the following command in your terminal:
   ```bash
   ollama run llama3 # or your preferred model
