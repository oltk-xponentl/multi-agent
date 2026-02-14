from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.prompts import RESEARCHER_PROMPT
from retrieval.retriever import retrieve_documents
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

def researcher_node(state: AgentState):
    print("--- RESEARCHER AGENT ---")
    plan = state["plan"]
    steps_to_execute = plan[:3] 
    
    findings = []
    logs = []

    for step in steps_to_execute:
        print(f"  > Researching: {step}")
        context = retrieve_documents(step, k=5)
        
        formatted_prompt = RESEARCHER_PROMPT.format(step=step, context=context)
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        
        # Gemini's response can be a list of parts; we need to concatenate them if so
        result = clean_gemini_response(response)
        
        findings.append(f"### Research for: {step}\n{result}\n")
        logs.append({
            "agent": "Researcher", 
            "message": f"Researched '{step}' - Retrieved {len(context)} chars of context."
        })

    return {
        "research_notes": findings,
        "logs": logs
    }