"""A lightweight node wrapper used by the debugger.

Each :class:`VirtualNode` wraps a runnable function and exposes hooks
for the debugger UI to observe pre/post execution state. The wrapper
also supports simple breakpoint semantics where execution can be
paused until the breakpoint flag is cleared.
"""

import traceback

from langgraph.graph import StateGraph
from langgraph._internal._runnable import RunnableCallable

import asyncio
from typing import Callable, Any, Self, Optional


class VirtualNode:
    """Represent a single node inside a virtual debugger graph.

    Attributes
    ----------
    name:
        The public name used when compiling the :class:`StateGraph`.

    func:
        A runnable callable that receives the graph state and returns a
        new/updated state mapping.
    """

    def __init__(
        self,
        name: str,
        func: RunnableCallable,
        on_pre_execute: Callable[[Self], Any],
        on_post_execute: Callable[[Self], Any],
        next_node: Optional[Self] = None,
        breakpoint: Optional[bool] = False,
    ):
        self.original_name = name
        self.name = name
        self.func = func
        self.next = next_node
        self.breakpoint = breakpoint
        self.input_state: dict[str, Any] = {}
        self.output_state: dict[str, Any] = {}
        self.on_pre_execute = on_pre_execute
        self.on_post_execute = on_post_execute
        self.error = ""

    def build(self, builder: StateGraph):
        """Add this virtual node to a :class:`StateGraph` builder.

        The builder stores the VirtualNode instance as the node's
        runnable. When the built graph is executed the runtime will call
        this object's ``__call__`` method.
        """
        builder.add_node(self.name, self)

    def set_breakpoint(self, value: bool):
        """Enable or disable the node's breakpoint state."""
        self.breakpoint = value

    def __repr__(self) -> str:
        return f'VirtualNode(name="{self.name}", func={self.func}, breakpoint={self.breakpoint})'

    async def __call__(self, *args, **kwds):
        """Invoke the node runnable with the provided graph state.

        The first positional argument is treated as the node's input
        state mapping. Before and after running the wrapped function the
        configured pre/post callbacks are awaited so the debugger can
        observe intermediate state.
        """
        self.input_state = args[0]
        result = self.input_state
        try:
            if self.breakpoint:
                # simple cooperative breakpoint: spin until cleared
                while self.breakpoint:
                    await asyncio.sleep(0.1)
            await self.on_pre_execute(self)
            result = self.func(self.input_state)
            self.output_state = result
        except Exception:
            self.error = traceback.format_exc()
            traceback.print_exc()
        await self.on_post_execute(self)
        return result
