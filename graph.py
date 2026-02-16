from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.planner import planner_node
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.verifier import verifier_node
from agents.defense import defense_node 

# 1. Initialize Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("defense", defense_node) 
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("verifier", verifier_node)

# 3. Define Edges
# Start with Defense
workflow.set_entry_point("defense")

# Conditional Edge for Defense
def check_safety(state: AgentState):
    if state.get("is_safe"):
        return "planner"
    return "end"

workflow.add_conditional_edges(
    "defense",
    check_safety,
    {
        "planner": "planner",
        "end": END
    }
)

# Standard Flow
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "verifier")

# Verifier Loop
def check_verification(state: AgentState):
    critique = state.get("critique", "").upper()
    revision_count = state.get("revision_number", 0)
    max_revs = state.get("max_revisions", 1)

    if "APPROVE" in critique:
        return "end"
    
    if revision_count >= max_revs:
        return "end"
    
    return "writer"

workflow.add_conditional_edges(
    "verifier",
    check_verification,
    {
        "writer": "writer",
        "end": END
    }
)

app_graph = workflow.compile()