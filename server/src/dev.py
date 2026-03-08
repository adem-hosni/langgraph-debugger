from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# 1. Define the State
# The state is the data structure passed between nodes.
# We use Annotated with operator.add to tell LangGraph to append to the list rather than overwrite it.
class AgentState(TypedDict):
    input_text: str
    category: str
    result: str
    # This helps us track the exact path the graph took for debugging
    node_history: Annotated[list[str], operator.add]


# 2. Define the Nodes
def categorize_input(state: AgentState):
    """Mock node that decides what kind of request this is."""
    text = state.get("input_text", "").lower()

    # Simple mock logic for routing
    if "weather" in text or "rain" in text or "temperature" in text:
        category = "weather"
    else:
        category = "general"

    return {"category": category, "node_history": ["categorize_input"]}


def fetch_weather(state: AgentState):
    """Mock node simulating an external API call."""
    return {
        "result": "The weather is currently sunny and 24°C.",
        "node_history": ["fetch_weather"],
    }


def general_response(state: AgentState):
    """Mock node simulating a standard LLM generation."""
    return {
        "result": f"I received your message: '{state['input_text']}'. How else can I help?",
        "node_history": ["general_response"],
    }


# 3. Define Conditional Routing Logic
def route_category(state: AgentState):
    """Router function that returns the name of the next node based on state."""
    if state["category"] == "weather":
        return "fetch_weather"
    return "general_response"


# 4. Build the Graph
builder = StateGraph(AgentState)

# Add nodes to the graph
builder.add_node("categorize", categorize_input)
builder.add_node("fetch_weather", fetch_weather)
builder.add_node("general_response", general_response)

# Set the starting point
builder.set_entry_point("categorize")

# Add conditional edges from the 'categorize' node
builder.add_conditional_edges(
    "categorize",
    route_category,
    {"fetch_weather": "fetch_weather", "general_response": "general_response"},
)

# Connect the leaf nodes to the end of the graph
builder.add_edge("fetch_weather", END)
builder.add_edge("general_response", END)

# 5. Compile the graph
mock_agent_graph = builder.compile(checkpointer=MemorySaver())

# ---------------------------------------------------------
# 6. Serve the graph using your new debugger package
# ---------------------------------------------------------
from app import serve, create_app
app = create_app(mock_agent_graph)

if __name__ == "__main__":
    # Import the serve function we created in your langgraph_debugger package

    # Run the debugger API
    serve("dev:app", port=2026, reload=True)
