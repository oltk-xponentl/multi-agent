from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.prompts import WRITER_PROMPT
import os
import time
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
    start_time = time.time()
    task = state["task"]
    research_notes = "\n\n".join(state["research_notes"])
    
    critique = state.get("critique")
    feedback_instruction = ""
    
    if critique and "REVISE" in critique:
        print(f"  ! Incorporating feedback: {critique}")
        feedback_instruction = f"\n\nIMPORTANT: The previous draft was rejected. \nFEEDBACK TO FIX: {critique}\nPlease fix these specific issues in the new draft."
    
    formatted_prompt = WRITER_PROMPT.format(
        task=task,
        research_notes=research_notes
    ) + feedback_instruction
    
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    draft = clean_gemini_response(response)
    
    end_time = time.time()
    latency = end_time - start_time
    
    # Token usage extraction with fallback for different response structures
    usage = response.usage_metadata or response.response_metadata.get("usage_metadata", {})
    input_tokens = usage.get("input_tokens", 0) or usage.get("prompt_token_count", 0)
    output_tokens = usage.get("output_tokens", 0) or usage.get("candidates_token_count", 0)
    
    current_rev = state.get("revision_number", 0)
    preview = draft[:300].replace("\n", " ") + "..."

    return {
        "draft": draft,
        "revision_number": current_rev + 1,
        "logs": [{"agent": "Writer", "message": f"**Draft Generated (Revision {current_rev + 1}):**\n\n_Preview: {preview}_"}],
        "metrics": [{
            "agent": "Writer",
            "latency": latency,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "status": "Success"
        }]
    }