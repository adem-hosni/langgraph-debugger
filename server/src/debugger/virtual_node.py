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
        self._name = f"VIRTUALNODE_{name}"
        self.func = func
        self.next = next_node
        self.breakpoint = breakpoint

    @property
    def name(self) -> str:
        if self._name == f"VIRTUALNODE_{START}":
            return START
        elif self._name == f"VIRTUALNODE_{END}":
            return END
        else:
            return self._name

    def build(self, builder: StateGraph):
        builder.add_node(self._name, self.func)

    def __repr__(self) -> str:
        return f'VirtualNode(name="{self._name}", func={self.func})'

    def __call__(self, *args, **kwds):
        print(f"Calling {self._name}")
        return self.func(*args, **kwds)
