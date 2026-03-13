import traceback

from langgraph.graph import StateGraph
from langgraph._internal._runnable import RunnableCallable

import asyncio
from typing import Callable, Any, Self, Optional


class VirtualNode:
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
        builder.add_node(self.name, self)

    def set_breakpoint(self, value: bool):
        self.breakpoint = value

    def __repr__(self) -> str:
        return f'VirtualNode(name="{self.name}", func={self.func}, breakpoint={self.breakpoint})'

    async def __call__(self, *args, **kwds):
        self.input_state = args[0]
        try:
            if self.breakpoint:
                while self.breakpoint:
                    await asyncio.sleep(0.1)
            await self.on_pre_execute(self)
            self.output_state = self.func(self.input_state)
            await self.on_post_execute(self)
            return self.output_state
        except Exception as err:
            self.error = err
            traceback.print_exc()
        return self.input_state
