from typing import Callable, Any

from langgraph.graph.state import CompiledStateGraph
from langgraph.typing import ContextT
from langgraph.graph._node import StateNodeSpec
from langgraph.graph import START, END, StateGraph

from .virtual_node import VirtualNode


class VirtualGraph:
    def __init__(self, graph: CompiledStateGraph, on_node_executed: Callable[[VirtualNode], Any]):
        self.graph = graph
        self._on_node_executed = on_node_executed

    def build_virtual_nodes(
        self, nodes: dict[str, StateNodeSpec[Any, None]]
    ) -> list[VirtualNode]:

        return [self.compile_node(*n) for n in nodes.items()]

    def link_virtual_edges(
        self, virtual_nodes: list[VirtualNode], edges: set[tuple[str, str]]
    ) -> VirtualNode:
        start_node: VirtualNode | None = None

        def findnode(name: str) -> VirtualNode:
            for node in virtual_nodes:
                if node.name == name:
                    return node

        for a, b in edges:
            if b == END:
                continue
            if a == START:
                start_node = findnode(b)
                continue
            findnode(a).next = findnode(b)

        return start_node

    def compile_node(
        self,
        node_id: str,
        node: StateNodeSpec[Any, ContextT],
    ) -> list[VirtualNode]:
        if isinstance(node.runnable, CompiledStateGraph):
            return self.build_virtual_nodes(node.runnable.builder.nodes)
        return VirtualNode(node_id, node.runnable.func, self._on_node_executed)

    def compile_graph(
        self, state: Any, virtual_nodes: VirtualNode, edges: set[tuple[str, str]]
    ) -> CompiledStateGraph:
        node = self.link_virtual_edges(virtual_nodes, edges)
        builder = StateGraph(state)
        node.build(builder)
        builder.add_edge(START, node.name)
        while node.next is not None:
            node.next.build(builder)
            if node.next == END:
                builder.add_edge(node.name, END)
            else:
                builder.add_edge(node.name, node.next.name)
            node = node.next
        return builder.compile()
