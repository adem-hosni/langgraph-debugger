from typing import TypedDict, Any


class StateHook(TypedDict):
    """
    Represents a state mutation emitted by a node during graph execution.

    Attributes
    ----------
    node_id : str
        Unique identifier of the node that produced the state update.

    updates : dict[str, Any]
        Mapping of state keys to their updated values. These updates are
        intended to be merged into the shared state object maintained by
        the execution graph.
    """

    node_id: str
    updates: dict[str, Any]
