from typing import Any
import traceback
from langgraph.graph.state import CompiledStateGraph

# Import the Pydantic models we just built
from schemas.graph import GraphData, NodeFlow, EdgeFlow, GraphNodeData, NodePosition
from debugger.virtual_graph import VirtualGraph


virtual_graph: VirtualGraph | None = None
graph: CompiledStateGraph | None = None

async def route_action(
    action_context: dict[str, Any], context: dict[str, CompiledStateGraph | Any]
) -> dict[str, Any]:
    """
    Routes incoming WebSocket messages to the appropriate graph actions.
    """
    try:
        action_type = action_context.get("action")
        result = {"type": "", "message": "", "data": {}}

        match action_type:
            case "fetch":
                print("fetching nodes..")
                result["type"] = "graph_data"
                result["data"] = get_graph_metadata(context["graph"])

                if not result["data"]:
                    result["type"] = "error"
                    result["message"] = "Failed to fetch nodes!"

            case "run":
                print("running nodes...")
                virtual_graph = VirtualGraph(context["graph"])

                nodes = virtual_graph.build_virtual_nodes(context["graph"].builder.nodes)
                graph = virtual_graph.compile_graph(
                    context["graph_state_schema"], nodes, context["graph"].builder.edges
                )
                
                graph.st

                result["type"] = "status"
                result["message"] = "Execution Started.."
            
            case "update_state":
                print("updating state...")
                

            case _:
                result["type"] = "error"
                result["message"] = "Unknown action type"
                print(f"Unknown action type {action_context}")

    except Exception as e:
        print("error:", e)
        traceback.print_exc()
        result["type"] = "error"
        result["message"] = str(e)

    return result


def get_graph_metadata(graph: CompiledStateGraph):
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

    return GraphData(nodes=nodes, edges=edges, execution_steps=[]).model_dump(
        mode="json", by_alias=True
    )
