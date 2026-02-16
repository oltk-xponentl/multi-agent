from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.prompts import RESEARCHER_PROMPT
from retrieval.retriever import retrieve_documents
import os
import time
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
    
    total_latency = 0
    total_input = 0
    total_output = 0

    for step in steps_to_execute:
        print(f"  > Researching: {step}")
        step_start = time.time()
        
        context = retrieve_documents(step, k=5)
        formatted_prompt = RESEARCHER_PROMPT.format(step=step, context=context)
        
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        result = clean_gemini_response(response)
        
        step_latency = time.time() - step_start
        total_latency += step_latency
        
        # Robust token usage extraction to handle different response structures
        usage = response.usage_metadata or response.response_metadata.get("usage_metadata", {})
        total_input += usage.get("input_tokens", 0) or usage.get("prompt_token_count", 0)
        total_output += usage.get("output_tokens", 0) or usage.get("candidates_token_count", 0)
        
        findings.append(f"### Research for: {step}\n{result}\n")
        logs.append({
            "agent": "Researcher", 
            "message": f"Researched '{step}' - Retrieved {len(context)} chars of context."
        })

    return {
        "research_notes": findings,
        "logs": logs,
        "metrics": [{
            "agent": "Researcher",
            "latency": total_latency,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "status": "Success"
        }]
    }