from typing import Any
import json
import traceback
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
)
from fastapi.requests import HTTPConnection
from langgraph.graph.state import CompiledStateGraph

from debugger.executor import Executor
from debugger.virtual_graph import VirtualGraph

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
    context = initialize_context(websocket, graph, graph_state_schema)
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


def initialize_context(
    websocket: WebSocket, graph: VirtualGraph, graph_state_schema: Any
) -> dict[str, Executor | VirtualGraph | CompiledStateGraph]:
    ctx = {"graph": graph, "graph_state_schema": graph_state_schema}
    send = lambda arg: websocket.send_text(json.dumps(arg))

    ctx["executor"] = Executor(
        ctx["graph"],
        ctx["graph_state_schema"],
        state_update_func=lambda data: send(
            {"type": "node_state_update", "data": data, "nodeId": data["nodeId"]}
        ),
    )
    ctx["virtual_graph"] = VirtualGraph(
        ctx["graph"],
        ctx["executor"].on_node_pre_executed,
        ctx["executor"].on_node_post_executed,
    )
    ctx["executor"].set_virtual_graph(ctx["virtual_graph"])

    return ctx
