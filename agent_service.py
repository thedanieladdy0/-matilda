import json, re
from ai.client import MatildaAI
from services.task_service import TaskService
from services.planner_service import PlannerService
from services.replanner_service import ReplannerService
from ai.prompts import AGENT_PROMPT

class AgentService:
    def __init__(self):
        self.ai = MatildaAI()

    def handle_message(self, user_message: str, history=None):
        """
        Handles user messages, maintains memory, and executes actions 
        like adding tasks or replanning the day.
        """
        
        # 1. Build the Memory (Context)
        # We turn the session history list into a string so the AI remembers the conversation
        context = ""
        if history:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in history])

        # 2. Combine History with the New Message
        # We tell the AI: "Here is what we talked about, and here is the new request"
        full_prompt = (
            f"Conversation History:\n{context}\n\n"
            f"User's Latest Message: {user_message}"
        )

        # 3. Generate the response using the combined prompt
        response = self.ai.generate_response(prompt=full_prompt, system_prompt=AGENT_PROMPT)
        
        # 4. Action Handling Logic (The "Brain" of the agent)
        try:
            # Look for JSON in the AI response
            match = re.search(r'(\{.*\})', response, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                action = data.get("action")
                params = data.get("params", {})
                
                if action == "ADD_TASK":
                    TaskService.create_task(
                        title=params.get("title"), 
                        priority=params.get("priority", "medium"), 
                        due_at=params.get("due_at"), 
                        estimate=params.get("estimate")
                    )
                    return "✅ I've added that to your list!"
                
                elif action == "REPLAN":
                    PlannerService.generate_daily_plan()
                    return "🪄 I've reorganized your day!"
                
                elif action == "CHAT":
                    return params.get("message", "I'm here to help!")
                
                return "I'm not sure how to do that yet!"
            
            # If no JSON is found, return the AI's plain text response
            return response
            
        except Exception: 
            # If anything crashes during JSON parsing, just return the raw AI response
            return response
