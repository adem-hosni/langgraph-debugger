from typing import Any, Literal, TypeAlias
from pydantic import ConfigDict

# Import the CamelBaseModel we defined earlier
# from langgraph_debugger.schemas.models import CamelBaseModel
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CamelBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


# ─── Types & Enums ────────────────────────────────────────────────────────

NodeStatusType: TypeAlias = Literal["idle", "running", "success", "error"]
GraphNodeType: TypeAlias = Literal["start", "agent", "tool", "end"]

# ─── Graph Node Data ──────────────────────────────────────────────────────


class GraphNodeData(CamelBaseModel):
    """The custom data payload inside a React Flow node."""

    label: str
    type: GraphNodeType
    status: NodeStatusType
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    state: dict[str, Any] | None = None
    error: str | None = None
    has_breakpoint: bool = False


# ─── React Flow Wrappers ──────────────────────────────────────────────────


class NodePosition(CamelBaseModel):
    """X/Y coordinates for React Flow node positioning."""

    x: float
    y: float


class NodeFlow(CamelBaseModel):
    """Maps to the `Node<GraphNodeData>` type from the reactflow library."""

    id: str
    type: str  # e.g., "graphNode" (React Flow's internal node type mapping)
    position: NodePosition
    data: GraphNodeData


class EdgeFlow(CamelBaseModel):
    """Maps to the `Edge` type from the reactflow library."""

    id: str
    source: str
    target: str
    animated: bool | None = None
    style: dict[str, Any] | None = None  # Maps to React CSSProperties


class ExecutionStep(CamelBaseModel):
    """Tracks the step-by-step execution history for the UI."""

    node_id: str  # Serializes to "nodeId" via CamelBaseModel
    status: NodeStatusType


# ─── Main Graph Data Response ─────────────────────────────────────────────


class GraphData(CamelBaseModel):
    """The master payload returned by the /api/graph/info endpoint."""

    nodes: list[NodeFlow]
    edges: list[EdgeFlow]
    execution_steps: list[ExecutionStep]  # Serializes to "executionSteps"