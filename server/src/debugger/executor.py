from langgraph.graph.state import CompiledStateGraph

from .virtual_graph import VirtualGraph
from .virtual_node import VirtualNode
from .types import StateHook

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
        self._statehooks: list[StateHook] = []

    def set_virtual_graph(self, virtual_graph: VirtualGraph):
        self.virtual_graph = virtual_graph
        self._compile_graph()

    def _compile_graph(self) -> None:
        nodes = self.virtual_graph.build_virtual_nodes(self.graph.builder.nodes)
        self.graph = self.virtual_graph.compile_graph(self._state_schema)

    async def execute(self, state: GraphState):
        asyncio.create_task(self.graph.ainvoke(state, stream_mode="updates"))

    def insert_state_hook(self, hook: StateHook):
        self._statehooks.append({**hook})

    async def on_node_pre_executed(self, node: VirtualNode):
        for idx in range(len(self._statehooks) - 1, -1, -1):
            hook = self._statehooks[idx]
            if hook["nodeId"] == node.name:
                node.input_state |= hook["updates"]
        
        packet = {
            "nodeId": node.name,
            "state": node.output_state,
            "input": node.input_state,
            "output": node.output_state,
            "error": node.error,
            "hasBreakpoint": node.breakpoint,
            "status": "running",
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
