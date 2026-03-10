from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. Define the Simplest State
# No Annotated reducers, just standard key overwrites.
class SimpleState(TypedDict):
    message: str
    status: str


# 2. Define Basic Sequential Nodes
def step_one(state: SimpleState):
    """Converts the message to uppercase."""
    return {"message": state["message"].upper(), "status": "step_one_completed"}


def step_two(state: SimpleState):
    """Appends a string to the message."""
    return {
        "message": state["message"] + " - PROCESSED",
        "status": "step_two_completed",
    }


# 3. Build a Linear Graph
builder = StateGraph(SimpleState)

builder.add_node("step_one", step_one)
builder.add_node("step_two", step_two)

# Straight line execution: START -> step_one -> step_two -> END
builder.add_edge(START, "step_one")
builder.add_edge("step_one", "step_two")
builder.add_edge("step_two", END)

# 4. Compile the graph (No checkpointer)
simple_graph = builder.compile()

# ---------------------------------------------------------
# 5. Serve the graph using your debugger package
# ---------------------------------------------------------
from app import serve, create_app

# Initial state matches the TypedDict exactly
initial_state = {"message": "hello langgraph", "status": "pending"}

# Mount it to your custom debugger API
app = create_app(simple_graph, initial_state, SimpleState)


if __name__ == "__main__":
    serve("dev:app", port=2026, reload=True)
