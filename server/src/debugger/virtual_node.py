from langgraph.graph import StateGraph, START, END
from langgraph._internal._runnable import RunnableCallable
from typing import Callable, Any, Self, Optional


class VirtualNode:
    def __init__(
        self,
        name: str,
        func: RunnableCallable,
        next_node: Optional[Self] = None,
        breakpoint: Optional[bool] = False,
    ):
        self.original_name = name
        self.name = name
        self.func = func
        self.next = next_node
        self.breakpoint = breakpoint

    def build(self, builder: StateGraph):
        builder.add_node(self.name, self)

    def __repr__(self) -> str:
        return f'VirtualNode(name="{self.name}", func={self.func})'

    def __call__(self, *args, **kwds):
        print(f"Calling {self.name}")
        return self.func(*args, **kwds)
