from typing import Literal
from langgraph.graph import StateGraph, END
from app.models.state import AgentState
from app.agents.scout import scout_node
from app.agents.hunter import hunter_node
from app.agents.architect import architect_node
from app.models.schema import LeadStatus

# 1. THE ROUTER LOGIC (The Decision Maker)
def router(state: AgentState) -> Literal["scout_node", "END"]:
    """
    Decides if the system should finish or go back for more data.
    """
    leads = state.get("final_leads", [])
    retry_count = state.get("retry_count", 0)

    # Path A: We found leads that need more info (Enrichment)
    if any(l.status == LeadStatus.REQUIRES_ENRICHMENT for l in leads):
        if retry_count < 3:
            print("🔄 Lead needs enrichment. Routing back to Scout...")
            return "scout_node"
    
    # Path B: We found absolutely nothing
    if not leads and retry_count < 2:
        print("🔄 No leads found. Routing back to Scout for broader search...")
        return "scout_node"

    # Path C: Success or Max Retries reached
    print("🏁 Research Complete. Delivering leads.")
    return "END"

# 2. BUILD THE GRAPH
workflow = StateGraph(AgentState)

# Add Nodes (The Workers)
workflow.add_node("scout_node", scout_node)
workflow.add_node("hunter_node", hunter_node)
workflow.add_node("architect_node", architect_node)

# Define the Fixed Edges (The standard flow)
workflow.set_entry_point("scout_node")
workflow.add_edge("scout_node", "hunter_node")
workflow.add_edge("hunter_node", "architect_node")

# Define the Conditional Edge (The "Brain" part)
# This says: After the architect finishes, run the 'router' function
workflow.add_conditional_edges(
    "architect_node",
    router,
    {
        "scout_node": "scout_node", # Loop back
        "END": END                 # Finished
    }
)

# 3. COMPILE
app = workflow.compile()