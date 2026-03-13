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
            {"type": "node_state_update", "data": data, "nodeId": data["nodeId"]}
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
