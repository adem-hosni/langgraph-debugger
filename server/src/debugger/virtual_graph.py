"""Create a virtual, debugger-friendly view of a compiled graph.

VirtualGraph wraps the nodes from a :class:`CompiledStateGraph` into
``VirtualNode`` instances that can report pre/post execution events and
support breakpoints. The compiled virtual graph can be recompiled into
an executable :class:`StateGraph` for running under the executor.
"""

from typing import Callable, Any, Generator, Optional, Union, List

from langgraph.graph.state import CompiledStateGraph
from langgraph.typing import ContextT
from langgraph.graph._node import StateNodeSpec
from langgraph.graph import START, END, StateGraph

from .virtual_node import VirtualNode


class VirtualGraph:
    """Manage virtual nodes and compile them into a runnable graph.

    Parameters
    ----------
    graph:
        The base :class:`CompiledStateGraph` containing node metadata.

    on_node_pre_executed, on_node_post_executed:
        Callables invoked by :class:`VirtualNode` instances to notify the
        debugger UI of execution progress.
    """

    def __init__(
        self,
        graph: CompiledStateGraph,
        on_node_pre_executed: Callable[[VirtualNode], Any],
        on_node_post_executed: Callable[[VirtualNode], Any],
    ):
        self.graph = graph
        self._on_node_pre_executed = on_node_pre_executed
        self._on_node_post_executed = on_node_post_executed
        self.start_node: Optional[VirtualNode] = None

    def build_virtual_nodes(
        self, nodes: Optional[dict[str, StateNodeSpec[Any, None]]] = None
    ) -> list[VirtualNode]:
        """Return a list of VirtualNode instances representing graph nodes.

        The returned list mirrors the input node mapping. Note that some
        nodes may represent subgraphs and therefore the compilation step
        may yield additional virtual nodes; callers should be aware of
        this when iterating the results.
        """
        return [self.compile_node(*n) for n in (nodes or self.graph.builder.nodes).items()]

    def link_virtual_edges(self) -> VirtualNode:
        """Link the compiled virtual nodes according to the graph edges.

        Returns the starting node of the linked virtual node chain.
        """
        node: Optional[VirtualNode] = None
        virtual_nodes = self.build_virtual_nodes()
        for a, b in self.graph.builder.edges:
            if b == END:
                continue
            if a == START:
                node = self[b, virtual_nodes]
                continue
            self[a, virtual_nodes].next = self[b, virtual_nodes]
        # node should be set to the entry node; keep typing explicit
        return node

    def compile_node(
        self,
        node_id: str,
        node: StateNodeSpec[Any, ContextT],
    ) -> Union[VirtualNode, List[VirtualNode]]:
        """Compile a single node spec into one or more VirtualNode(s).

        If the node represents a nested/compiled subgraph the method
        returns a list of VirtualNode instances representing the inner
        graph. Otherwise a single VirtualNode is returned.
        """
        if isinstance(node.runnable, CompiledStateGraph):
            return self.build_virtual_nodes(node.runnable.builder.nodes)
        return VirtualNode(
            node_id,
            node.runnable.func,
            self._on_node_pre_executed,
            self._on_node_post_executed,
        )

    def compile_graph(self, state: Any) -> CompiledStateGraph:
        """Build and compile a :class:`StateGraph` from the virtual nodes.

        The returned :class:`CompiledStateGraph` is ready for async
        invocation. The ``state`` parameter provides the initial state
        or schema used by the graph builder.
        """
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
        """Lookup a virtual node by name.

        Supports two forms:

        - ``vg["nodeName"]`` to search the default virtual node iterable.
        - ``vg["nodeName", virtual_nodes]`` to search an explicit
          iterable returned by :meth:`build_virtual_nodes`.
        """
        if isinstance(key, str):
            target_node = key
            virtual_nodes = self
        if isinstance(key, slice) or isinstance(key, tuple):
            target_node, virtual_nodes = key
        for node in virtual_nodes:
            if node.name == target_node:
                return node
