from typing import Any

from langgraph.graph.state import CompiledStateGraph
from langgraph.typing import ContextT
from langgraph.graph._node import StateNodeSpec
from langgraph.graph import START, END, StateGraph

from .virtual_node import VirtualNode


class VirtualGraph:
    def __init__(self, graph: CompiledStateGraph):
        self.graph = graph

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
                if node.name == f"VIRTUALNODE_{name}":
                    return node

        for a, b in edges:
            if b == END:
                findnode(a).next = VirtualNode(END, lambda arg: arg)
                continue
            if a == START:
                start_node = VirtualNode(START, lambda arg: arg)
                start_node.next = findnode(b)
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
        return VirtualNode(node_id, node.runnable)

    def compile_graph(
        self, state: Any, virtual_nodes: VirtualNode, edges: set[tuple[str, str]]
    ) -> CompiledStateGraph:
        node = self.link_virtual_edges(virtual_nodes, edges)
        builder = StateGraph(state)
        node.build(builder)
        while node.next is not None:
            node.next.build(builder)
            if node.next == f"VIRTUALNODE_{END}":
                builder.add_edge(node.name, END)
            else:
                builder.add_edge(node.name, node.next.name)
            node = node.next
        return builder.compile()
