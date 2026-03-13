from langgraph.graph.state import CompiledStateGraph

from .virtual_graph import VirtualGraph
from .virtual_node import VirtualNode

import asyncio
from typing import TypeAlias, Any


GraphState: TypeAlias = dict[str, Any]


class Executor:
    def __init__(
        self,
        graph: CompiledStateGraph,
        state_schema: Any,
        state_update_func: Any,
    ):
        self.virtual_graph: VirtualGraph | None = None
        self.graph: CompiledStateGraph | None = graph
        self._state_schema = state_schema
        self._state_update_func = state_update_func

    def set_virtual_graph(self, virtual_graph: VirtualGraph):
        self.virtual_graph = virtual_graph
        self._compile_graph()

    def _compile_graph(self) -> None:
        nodes = self.virtual_graph.build_virtual_nodes(self.graph.builder.nodes)
        self.graph = self.virtual_graph.compile_graph(self._state_schema)

    async def execute(self, state: GraphState):
        asyncio.create_task(self.graph.ainvoke(state, stream_mode="updates"))

    async def on_node_pre_executed(self, node: VirtualNode):
        packet = {
            "nodeId": node.name,
            "state": node.output_state,
            "input": node.input_state,
            "output": node.output_state,
            "error": node.error,
            "hasBreakpoint": node.breakpoint,
            "status": "running",
            "label": f"Running {node.name}",
        }
        await self._state_update_func(packet)

    async def on_node_post_executed(self, node: VirtualNode):
        packet = {
            "nodeId": node.name,
            "state": node.output_state,
            "input": node.input_state,
            "output": node.output_state,
            "error": node.error,
            "hasBreakpoint": node.breakpoint,
            "status": "error" if node.error else "success",
            "label": node.name,
        }
        await self._state_update_func(packet)
