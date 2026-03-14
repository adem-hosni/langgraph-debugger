# Usage

This page explains typical runtime workflows and how to operate the
debugger UI.

Common Workflows

- Run a graph: open the UI, select or compose a graph, then click the
  execution button. Execution packets will stream back to the UI and
  the state inspector will update.
- Set breakpoints: toggle a node's breakpoint in the UI; the server's
  VirtualNode will pause before executing the node until the breakpoint
  is cleared.
- Inject state updates: the UI can send small state hooks which are
  merged into a node's input state before that node runs.

Websocket messages

- Control messages: start/stop/run/step are sent from client to server
  to control execution.
- State packets: server -> client messages that contain fields like
  `nodeId`, `state`, `input`, `output`, `error`, `hasBreakpoint`, and
  `status`. These are used to render node states and logs.

Troubleshooting

- If the UI shows stale state, restart the client and re-run the
  scenario to ensure a fresh graph compilation.
- Exceptions in node handlers are captured and sent in the `error`
  field; inspect server logs for full tracebacks.
