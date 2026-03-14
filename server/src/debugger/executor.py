"""Executor wrapper used by the debugger to run a compiled state graph.

This module exposes :class:`Executor` which wires a :class:`VirtualGraph`
to a :class:`langgraph.graph.state.CompiledStateGraph`. It also provides
hooks and callbacks used by the debugger UI to observe execution
progress and state changes.
"""

from langgraph.graph.state import CompiledStateGraph

from .virtual_graph import VirtualGraph
from .virtual_node import VirtualNode
from .types import StateHook

import asyncio
from typing import TypeAlias, Any, Callable, Optional


GraphState: TypeAlias = dict[str, Any]


class Executor:
    """Manage execution of a compiled state graph with debugger hooks.

    Parameters
    ----------
    graph:
        A pre-compiled :class:`CompiledStateGraph` instance used as the
        base for execution.

    state_schema:
        The schema/initial state used when compiling virtual graphs.

    state_update_func:
        Async callable that will be invoked with execution packets. This
        function is expected to accept a single mapping describing node
        status/state and forward it to the frontend (for example over a
        websocket).
    """

    def __init__(
        self,
        graph: CompiledStateGraph,
        state_schema: Any,
        state_update_func: Callable[[dict], Any],
    ):
        self.virtual_graph: Optional[VirtualGraph] = None
        self.graph: Optional[CompiledStateGraph] = graph
        self._state_schema = state_schema
        self._state_update_func = state_update_func
        self._statehooks: list[StateHook] = []

    def set_virtual_graph(self, virtual_graph: VirtualGraph):
        """Attach a :class:`VirtualGraph` and compile a runnable graph.

        The attached virtual graph is used to build lightweight
        VirtualNode wrappers around the compiled graph's node
        definitions. After attaching, the executor recompiles the
        graph using the current state schema so the resulting
        :class:`CompiledStateGraph` is ready to run.
        """
        self.virtual_graph = virtual_graph
        self._compile_graph()

    def _compile_graph(self) -> None:
        """Recompile the underlying graph using the current virtual graph.

        The method ensures the executor's ``self.graph`` points to a
        freshly compiled :class:`CompiledStateGraph` built from the
        virtual representation and the configured state schema.
        """
        # Build virtual nodes (side-effect: allows VirtualNode instances
        # to be prepared). The returned value is not directly used here
        # but the call keeps the VirtualGraph's internal node structures
        # populated for later linkage.
        _ = self.virtual_graph.build_virtual_nodes(self.graph.builder.nodes)
        self.graph = self.virtual_graph.compile_graph(self._state_schema)

    async def execute(self, state: GraphState):
        """Start graph execution asynchronously.

        Execution uses the compiled graph's async entry point and runs in a
        detached task so the caller (typically a websocket handler) can
        continue processing while the graph runs. The executor uses the
        graph's streaming mode to emit incremental state updates.
        """
        asyncio.create_task(self.graph.ainvoke(state, stream_mode="updates"))

    def insert_state_hook(self, hook: StateHook):
        """Insert a state hook which will be applied to matching nodes.

        Hooks are inspected just prior to a node's execution and merged
        into the node's input state when the node's identifier matches
        the hook's ``nodeId``.
        """
        # store a shallow copy to avoid accidental mutation by callers
        self._statehooks.append({**hook})

    async def on_node_pre_executed(self, node: VirtualNode):
        """Called by a VirtualNode before it runs.

        Applies any matching state hooks (last-in-first-applied) and then
        forwards a running-state packet to the configured
        ``state_update_func`` so observers can show progress.
        """
        for idx in range(len(self._statehooks) - 1, -1, -1):
            hook = self._statehooks[idx]
            if hook["nodeId"] == node.name:
                # merge the hook updates into the node's input state
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
        """Called after a VirtualNode finishes execution.

        Sends a status packet describing the node's output, any error
        traceback, and whether the node was stopped on a breakpoint.
        """
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
