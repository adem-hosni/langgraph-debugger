from typing import Callable, Any, Generator, Optional

from langgraph.graph.state import CompiledStateGraph
from langgraph.typing import ContextT
from langgraph.graph._node import StateNodeSpec
from langgraph.graph import START, END, StateGraph

from .virtual_node import VirtualNode


class VirtualGraph:
    def __init__(
        self,
        graph: CompiledStateGraph,
        on_node_pre_executed: Callable[[VirtualNode], Any],
        on_node_post_executed: Callable[[VirtualNode], Any],
    ):
        self.graph = graph
        self._on_node_pre_executed = on_node_pre_executed
        self._on_node_post_executed = on_node_post_executed
        self.start_node: VirtualNode | None = None

    def build_virtual_nodes(
        self, nodes: Optional[dict[str, StateNodeSpec[Any, None]]] = None
    ) -> list[VirtualNode]:

        return [
            self.compile_node(*n) for n in (nodes or self.graph.builder.nodes).items()
        ]

    def link_virtual_edges(self) -> VirtualNode:
        node: VirtualNode | None = None
        virtual_nodes = self.build_virtual_nodes()

        for a, b in self.graph.builder.edges:
            if b == END:
                continue
            if a == START:
                node = self[b, virtual_nodes]
                continue
            self[a, virtual_nodes].next = self[b, virtual_nodes]

        return node

    def compile_node(
        self,
        node_id: str,
        node: StateNodeSpec[Any, ContextT],
    ) -> list[VirtualNode]:
        if isinstance(node.runnable, CompiledStateGraph):
            return self.build_virtual_nodes(node.runnable.builder.nodes)
        return VirtualNode(
            node_id,
            node.runnable.func,
            self._on_node_pre_executed,
            self._on_node_post_executed,
        )

    def compile_graph(self, state: Any) -> CompiledStateGraph:
        print("compiling...")
        node = self.start_node = self.link_virtual_edges()
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

    def __iter__(self) -> Generator[VirtualNode]:
        node = self.start_node
        if not node:
            yield
        while node.next is not None:
            yield node
            node = node.next
        yield node

    def __getitem__(self, key) -> VirtualNode:
        if isinstance(key, str):
            target_node = key
            virtual_nodes = self
        if isinstance(key, slice) or isinstance(key, tuple):
            target_node, virtual_nodes = key

        for node in virtual_nodes:
            if node.name == target_node:
                return node
