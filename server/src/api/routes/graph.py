from typing import Any
import json
import traceback
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Request,
    HTTPException,
)
from fastapi.requests import HTTPConnection
from langgraph.graph.state import CompiledStateGraph
from debugger.executor import Executor
from debugger.virtual_graph import VirtualGraph

# Import the Pydantic models we just built
from schemas.graph import GraphData, NodeFlow, EdgeFlow, GraphNodeData, NodePosition

from services.action_router import route_action

ws_router = APIRouter(tags=["Graph Debugger"])
prefix = "/ws"


def get_graph(conn: HTTPConnection) -> CompiledStateGraph:
    return conn.app.state.graph


def get_graph_state(conn: HTTPConnection) -> CompiledStateGraph:
    return conn.app.state.graph_state_schema


@ws_router.websocket("/graph")
async def ws_endpoint(
    websocket: WebSocket,
    graph: CompiledStateGraph = Depends(get_graph),
    graph_state_schema: Any = Depends(get_graph_state),
):
    await websocket.accept()
    context = {"graph": graph, "graph_state_schema": graph_state_schema}
    send = lambda arg: websocket.send_text(json.dumps(arg))
    context["executor"] = Executor(
        context["graph"],
        context["graph_state_schema"],
        state_update_func=lambda data: send(
            {"type": "node_state_update", "data": data}
        ),
    )
    context["virtual_graph"] = VirtualGraph(
        context["graph"],
        context["executor"].on_node_pre_executed,
        context["executor"].on_node_post_executed,
    )
    context["executor"].set_virtual_graph(context["virtual_graph"])
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            result = await route_action(
                data, context, lambda arg: websocket.send_text(json.dumps(arg))
            )

            if result and result["type"]:
                await websocket.send_text(json.dumps(result))
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as err:
        traceback.print_exc()


@ws_router.get("/info", response_model=GraphData)
async def get_graph_metadata(graph: CompiledStateGraph = Depends(get_graph)):
    """
    Inspects the injected LangGraph and dynamically generates the React Flow
    nodes and edges with a hierarchical auto-layout engine.
    """
    try:
        drawable_graph = graph.get_graph()

        nodes: list[NodeFlow] = []
        edges: list[EdgeFlow] = []

        # ─── 1. HIERARCHICAL AUTO-LAYOUT ENGINE ───

        # Track which level (depth) each node belongs to
        node_levels: dict[str, int] = {}
        queue = [("__start__", 0)]

        # BFS traversal to assign depth levels
        while queue:
            current_node, depth = queue.pop(0)

            # If we haven't visited this node, or we found a shorter path to it
            if current_node not in node_levels:
                node_levels[current_node] = depth

                # Find all children of this node
                children = [
                    edge.target
                    for edge in drawable_graph.edges
                    if edge.source == current_node
                ]

                for child in children:
                    queue.append((child, depth + 1))

        # Group nodes by their depth level
        levels_map: dict[int, list[str]] = {}
        for node_id in drawable_graph.nodes.keys():
            # Fallback to level 0 if a node is somehow disconnected
            lvl = node_levels.get(node_id, 0)
            levels_map.setdefault(lvl, []).append(node_id)

        # Calculate exact X/Y positions
        positions: dict[str, NodePosition] = {}
        X_CENTER = 400
        X_SPACING = 250
        Y_SPACING = 130
        START_Y = 30

        for level, group in levels_map.items():
            num_nodes = len(group)
            # Calculate the starting X so the group is perfectly centered
            start_x = X_CENTER - ((num_nodes - 1) * X_SPACING / 2)

            for index, node_id in enumerate(group):
                positions[node_id] = NodePosition(
                    x=start_x + (index * X_SPACING), y=START_Y + (level * Y_SPACING)
                )

        # ─── 2. MAP NODES ───

        for node_id, node_data in drawable_graph.nodes.items():
            if node_id == "__start__":
                node_type = "start"
                label = "START"
            elif node_id == "__end__":
                node_type = "end"
                label = "END"
            elif "tool" in node_id.lower():
                node_type = "tool"
                label = node_id.replace("_", " ").title()
            else:
                node_type = "agent"
                label = node_id.replace("_", " ").title()

            nodes.append(
                NodeFlow(
                    id=node_id,
                    type="graphNode",
                    position=positions.get(node_id, NodePosition(x=400, y=30)),
                    data=GraphNodeData(
                        label=label,
                        type=node_type,
                        status="idle",
                        input={},
                        output={},
                        state={},
                        error=None,
                    ),
                )
            )

        # ─── 3. MAP EDGES ───

        for edge in drawable_graph.edges:
            edge_id = f"e-{edge.source}-{edge.target}"
            style = {"stroke": "hsl(0, 0%, 40%)"}
            animated = False

            if edge.source == "__start__":
                style["stroke"] = "hsl(142, 71%, 45%)"
                animated = True

            edges.append(
                EdgeFlow(
                    id=edge_id,
                    source=edge.source,
                    target=edge.target,
                    animated=animated,
                    style=style,
                )
            )

        # ─── 4. RETURN PAYLOAD ───
        return GraphData(nodes=nodes, edges=edges, execution_steps=[])

    except Exception as e:
        print(f"Error parsing graph structure: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse graph structure.")
