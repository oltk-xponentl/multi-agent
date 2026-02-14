from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.prompts import WRITER_PROMPT
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model=os.environ.get("MODEL_NAME", "gemini-3-flash-preview"),
    temperature=0.2, 
    google_api_key=os.environ["GOOGLE_API_KEY"]
)

def clean_gemini_response(response):
    content = response.content
    if isinstance(content, list):
        full_text = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                full_text.append(part["text"])
            elif isinstance(part, str):
                full_text.append(part)
        return "".join(full_text)
    return str(content)

def writer_node(state: AgentState):
    print("--- WRITER AGENT ---")
    task = state["task"]
    research_notes = "\n\n".join(state["research_notes"])
    
    # Check for previous critique (Self-Correction Logic)
    critique = state.get("critique")
    feedback_instruction = ""
    
    if critique and "REVISE" in critique:
        print(f"  ! Incorporating feedback: {critique}")
        feedback_instruction = f"\n\nIMPORTANT: The previous draft was rejected. \nFEEDBACK TO FIX: {critique}\nPlease fix these specific issues in the new draft."
    
    # Append feedback to prompt
    formatted_prompt = WRITER_PROMPT.format(
        task=task,
        research_notes=research_notes
    ) + feedback_instruction
    
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    
    # Gemini's response can be a list of parts; we need to concatenate them if so
    draft = clean_gemini_response(response)
    
    current_rev = state.get("revision_number", 0)
    
    return {
        "draft": draft,
        "revision_number": current_rev + 1,
        "logs": [{"agent": "Writer", "message": f"Drafted response (Revision {current_rev + 1})"}]
    }