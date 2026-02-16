from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.prompts import VERIFIER_PROMPT
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

def verifier_node(state: AgentState):
    print("--- VERIFIER AGENT ---")
    start_time = time.time()
    draft = state["draft"]
    research_notes = "\n".join(state["research_notes"])
    
    formatted_prompt = VERIFIER_PROMPT.format(draft=draft, research_notes=research_notes)
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    critique = clean_gemini_response(response).strip()
    
    end_time = time.time()
    latency = end_time - start_time
    
    # Robust token usage extraction to handle different response structures
    usage = response.usage_metadata or response.response_metadata.get("usage_metadata", {})
    input_tokens = usage.get("input_tokens", 0) or usage.get("prompt_token_count", 0)
    output_tokens = usage.get("output_tokens", 0) or usage.get("candidates_token_count", 0)
    
    return {
        "critique": critique,
        "logs": [{"agent": "Verifier", "message": f"Verification Result: {critique}"}],
        "metrics": [{
            "agent": "Verifier",
            "latency": latency,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "status": "Success"
        }]
    }