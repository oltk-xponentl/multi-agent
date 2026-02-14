from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.prompts import PLANNER_PROMPT
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Model
llm = ChatGoogleGenerativeAI(
    model=os.environ.get("MODEL_NAME", "gemini-3-flash-preview"),
    temperature=0,
    google_api_key=os.environ["GOOGLE_API_KEY"]
)

def clean_gemini_response(response):
    """Helper to extract clean text from complex Gemini 3 responses."""
    content = response.content
    
    # Case 1: List of parts (e.g., [{'type': 'text', 'text': '...'}])
    if isinstance(content, list):
        full_text = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                full_text.append(part["text"])
            elif isinstance(part, str):
                full_text.append(part)
        return "".join(full_text)
        
    # Case 2: Standard string
    return str(content)

def planner_node(state: AgentState):
    """
    Planner Agent: Decomposes the task into a research plan.
    """
    print("--- PLANNER AGENT ---")
    task = state["task"]
    
    formatted_prompt = PLANNER_PROMPT.format(task=task)
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    
    # 1. Clean the response
    content = clean_gemini_response(response)
    
    # 2. Strip Markdown
    content = content.replace("```json", "").replace("```", "").strip()
    
    try:
        plan_data = json.loads(content)
        steps = plan_data.get("steps", [])
    except json.JSONDecodeError:
        # Fallback
        steps = [task] 
        print(f"Error parsing Planner JSON. Raw content: {content[:100]}...")

    return {
        "plan": steps,
        "logs": [{"agent": "Planner", "message": f"Generated {len(steps)} step plan."}]
    }