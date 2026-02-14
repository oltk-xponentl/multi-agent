from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.planner import planner_node
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.verifier import verifier_node

# 1. Initialize Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("verifier", verifier_node)

# 3. Define Edges (Linear Flow)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "verifier")

# 4. Conditional Logic (Verifier Loop)
def check_verification(state: AgentState):
    """
    Router: Decides if we finish or revise based on Verifier output.
    """
    critique = state.get("critique", "").upper()
    revision_count = state.get("revision_number", 0)
    max_revs = state.get("max_revisions", 1)

    # Success Condition
    if "APPROVE" in critique:
        return "end"
    
    # Safety Valve (Prevent infinite loops and cost)
    if revision_count >= max_revs:
        return "end"
    
    # Loop back to Writer
    return "writer"

workflow.add_conditional_edges(
    "verifier",
    check_verification,
    {
        "writer": "writer",
        "end": END
    }
)

# 5. Compile
app_graph = workflow.compile()