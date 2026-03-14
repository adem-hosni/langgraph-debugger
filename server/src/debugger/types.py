"""Types used by the debugger virtual graph/executor.

These small, focused types document the shape of messages exchanged
between the server-side executor/virtual graph and any front-end
debugger components. Keeping the field names aligned with the JSON
packets used by the UI (camelCase) avoids accidental mismatches.
"""

from typing import TypedDict, Any


class StateHook(TypedDict):
    """TypedDict describing a mutation hook applied to the graph state.

    Fields
    ------
    nodeId: str
        Identifier of the node the hook targets (camelCase to match JSON
        messages consumed by the client).

    updates: dict[str, Any]
        A mapping of state keys -> new values that should be merged into
        the graph state before the target node executes.
    """

    nodeId: str
    updates: dict[str, Any]
