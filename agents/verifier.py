from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.prompts import VERIFIER_PROMPT
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model=os.environ.get("MODEL_NAME", "gemini-3-flash-preview"),
    temperature=0,
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

def verifier_node(state: AgentState):
    print("--- VERIFIER AGENT ---")
    draft = state["draft"]
    research_notes = "\n".join(state["research_notes"])
    
    formatted_prompt = VERIFIER_PROMPT.format(draft=draft, research_notes=research_notes)
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    
    # Gemini's response can be a list of parts; we need to concatenate them if so
    critique = clean_gemini_response(response).strip()
    
    return {
        "critique": critique,
        "logs": [{"agent": "Verifier", "message": f"Verification Result: {critique}"}]
    }