# Client Components

This document describes every component in the `client/src/components/` directory, organized by domain.

---

## Graph Components (`components/graph/`)

### GraphDebugger (`GraphDebugger.tsx`)
The main orchestrator for the graph debugger view.

**Responsibilities**:
- Manages graph data state, execution progress, breakpoints, and selected node
- Subscribes to WebSocket events (`graph_data`, `node_state_update`)
- Sends WebSocket actions (fetch, run, set_breakpoint, remove_breakpoint, update_state)
- Computes node states based on current execution step
- Handles keyboard shortcuts (Space, Arrow keys, R, Escape)
- Auto-opens the state inspector when a node encounters an error
- Implements auto-play with breakpoint-aware pausing (1s step interval)

**Key State**:
- `graphData: GraphData | null` — The complete graph layout
- `currentStep: number` — Current position in the execution steps array
- `isPlaying: boolean` — Whether auto-play is active
- `selectedNode: { id, data } | null` — Node selected for inspection
- `breakpoints: Set<string>` — Set of node IDs with breakpoints

**Subscriptions**:
- Uses `useGraphWebSocket()` for `send`, `connected`, `subscribe`, `subscribeNodeState`

### GraphNode (`GraphNode.tsx`)
Custom React Flow node component (memoized).

**Rendering**:
- Styled card with border color based on status (running=blue, success=green, error=red, idle=gray)
- Type-specific icons: START→Play (green), Agent→Bot (blue), Tool→Wrench (amber), END→Square (gray)
- Status indicators: checkmark (success), alert triangle (error), spinner (running)
- **Breakpoint toggle**: Circle button on the left side of agent/tool nodes
- Connection handles: target (top) for all except START, source (bottom) for all except END

**Props**: Receives `NodeProps<GraphNodeData>` from React Flow, which includes `data`, `selected`, etc.

### ExecutionControls (`ExecutionControls.tsx`)
Floating control bar at the bottom center of the graph view.

**Controls**:
- Reset (R) — Resets all execution state
- Step Back (←) — Moves to previous step (disabled at step 0)
- Play/Pause (Space) — Toggles auto-execution (pulse animation when playing)
- Step Forward (→) — Advances to next step (disabled at last step)

**Display**:
- Connection indicator: green dot (connected) or red pulsing dot (disconnected)
- Step counter: `currentStep + 1 / totalSteps` with mini progress bar
- Breakpoint count badge (shown when breakpoints exist, clickable to clear all)

**Props**: `currentStep`, `totalSteps`, `isPlaying`, `isPaused`, `breakpointCount`, `connected`, and callback handlers.

### StateInspector (`StateInspector.tsx`)
Side panel (320px, right side) for inspecting and editing node state.

**Sections**:
- **Header**: Node label, status dot (colored), status/type/breakpoint badges
- **Error**: Red alert card with stack trace (auto-opened on error)
- **Tabs**: Input (editable), Output (read-only)

**JsonViewer** (inline component):
- Read mode: Formatted JSON with copy button (checkmark feedback)
- Edit mode: Textarea with JSON validation (parse errors shown inline)
- Editable for agent/tool nodes; save sends `update_state` action
- Copy, edit (pencil), save (checkmark), cancel (undo) buttons

**Actions**:
- Rerun button: Re-executes the selected node
- Close button / Escape: Dismisses the panel

---

## Chat Components (`components/chat/`)

### ChatInput (`ChatInput.tsx`)
Message input area with file attachment support.

**Features**:
- Auto-resizing textarea (up to 200px)
- Drag-and-drop file attachment with visual highlight
- File type detection by extension → type-specific icons (code, data, image, document)
- File badges with name, size, and remove button
- Enter to send, Shift+Enter for newline
- Send button with loading spinner during transmission
- Visual states: focused (ring), dragging (blue border+scale), idle (shadow)

**Sub-components**: ModeSelector embedded below input

### ChatMessage (`ChatMessage.tsx`)
Renders a single message bubble.

**Variants**:
- **User**: `User` icon, plain text content, file attachment badges
- **Assistant**: `Bot` icon with `Sparkles`, optional `ThinkingBlock`, `ToolCallBlock` list, `MarkdownRenderer`

**Props**: `message: ChatMessage`, `index: number` (for staggered animation)

### ChatSidebar (`ChatSidebar.tsx`)
Left sidebar with session list and controls.

**Sections**:
- **New Chat button**: Creates a new session
- **Session list**: Scrollable, grouped by date, with active session highlighting
- **Footer**: Theme toggle (cycles light→dark→system), Settings gear button

**Props**: `open`, `onSettingsOpen`, `theme`, `onThemeToggle`

### MarkdownRenderer (`MarkdownRenderer.tsx`)
Renders markdown content from AI responses.

**Components**:
- `ReactMarkdown` with custom overrides for code, headings, paragraphs, lists, blockquotes
- **CodeBlock** (inline sub-component): Syntax-highlighted with Prism (Dracula theme), copy button with checkmark/transition, language label
- **Inline code**: Muted background with border

### ModelSelector (`ModelSelector.tsx`)
Dropdown for selecting the AI model.

**Features**:
- Lists built-in models (GPT-4o, Claude, Gemini, GPT-4o Mini)
- "Custom" badge on user-added models
- "Add custom model" option opens a dialog
- Dialog: text input + add button, lists existing custom models with delete button

**Props**: None (reads from `useChatContext`)

### ModeSelector (`ModeSelector.tsx`)
Dropdown for selecting the chat mode.

**Modes**:
| Mode | Icon | Description |
|---|---|---|
| Default | MessageSquare | Balanced responses |
| Deep Thinking | Brain | Step-by-step reasoning |
| Research | Search | In-depth analysis |
| Creative | Lightbulb | Imaginative |
| Concise | Zap | Brief |

**Props**: None (reads from `useChatContext`)

### SettingsModal (`SettingsModal.tsx`)
Dialog for configuring system instructions.

**Features**:
- Textarea for system prompt (default: helpful AI assistant persona)
- 6 rows, monospace font, resizable

**Props**: `open`, `onOpenChange`

### ThinkingBlock (`ThinkingBlock.tsx`)
Collapsible section showing AI's reasoning chain.

**Features**:
- Brain icon, "Thought for X seconds" label
- Animated expand/collapse with grid-rows transition
- Styled with amber-tinted background

**Props**: `content: string`

### ToolCallBlock (`ToolCallBlock.tsx`)
Collapsible block for each tool invocation.

**Features**:
- Type-specific icons (globe, code, database, search)
- Status badges: Done (green), Running (blue, spinning), Error (red)
- Expandable: shows tool input and output as formatted JSON
- Staggered entrance animation

**Props**: `tool: ToolCall`, `index?: number`

---

## Top-Level Components

### GraphWsProvider (`GraphWsProvider.tsx`)
Wraps the app with WebSocket context.

```tsx
<GraphWsContext.Provider value={useGraphWsProvider()}>
  {children}
</GraphWsContext.Provider>
```

### NavLink (`NavLink.tsx`)
Wrapper around React Router's `NavLink` with enhanced className support.

**Props**: `className`, `activeClassName`, `pendingClassName`, `to`, plus all standard `NavLinkProps`.

---

## UI Components (`components/ui/`)

The project includes 50+ [shadcn/ui](https://ui.shadcn.com/) primitive components, all generated via the shadcn CLI:

`accordion`, `alert-dialog`, `alert`, `aspect-ratio`, `avatar`, `badge`, `breadcrumb`, `button`, `calendar`, `card`, `carousel`, `chart`, `checkbox`, `collapsible`, `command`, `context-menu`, `dialog`, `drawer`, `dropdown-menu`, `form`, `hover-card`, `input-otp`, `input`, `label`, `menubar`, `navigation-menu`, `pagination`, `popover`, `progress`, `radio-group`, `resizable`, `scroll-area`, `select`, `separator`, `sheet`, `sidebar`, `skeleton`, `slider`, `sonner`, `switch`, `table`, `tabs`, `textarea`, `toast`, `toaster`, `toggle-group`, `toggle`, `tooltip`, `use-toast`

These are standard Radix UI-based components with Tailwind styling. They are used throughout the chat and graph components for consistent UI.
