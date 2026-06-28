# Client Hooks

This document describes all custom React hooks in `client/src/hooks/`.

---

## `use-chat.tsx` — Chat State Management

### Purpose
Provides global chat state via React Context, including sessions, messages, models, and chat modes.

### Exports

| Export | Type | Description |
|---|---|---|
| `ChatProvider` | Component | Context provider wrapping the chat app |
| `useChatContext` | Hook | Returns the current chat context value |

### Context Value (`ChatContextType`)

```typescript
interface ChatContextType {
  sessions: ChatSession[];              // All chat sessions
  activeSessionId: string;              // Currently selected session ID
  activeSession: ChatSession;           // Currently selected session object
  models: AIModel[];                    // Available AI models
  selectedModel: string;                // Currently selected model value
  mode: ChatMode;                       // Current chat mode
  isLoading: boolean;                   // Initial data loading
  isSending: boolean;                   // Message transmission in progress
  setSelectedModel: (m: string) => void;
  setMode: (m: ChatMode) => void;
  addCustomModel: (label: string) => void;
  removeCustomModel: (value: string) => void;
  switchSession: (id: string) => void;
  createNewChat: () => void;
  deleteChat: (id: string) => void;
  sendMessage: (content: string, attachments?: Attachment[]) => void;
}
```

### Implementation Details

**Initialization** (`useEffect` on mount):
- Fetches sessions and models in parallel via `mockApi.sessions.fetch()` and `mockApi.models.fetch()`
- Sets `activeSessionId` to the first session (or empty string if none)
- Uses a `cancelled` flag to prevent state updates after unmount

**`sendMessage`**:
- Guards against concurrent sends (`if (isSending) return`)
- Calls `mockApi.messages.send()` with sessionId, content, attachments, model, and mode
- On success, updates the session's messages array with both user and assistant messages
- Updates the session title if the response includes `updatedSessionTitle`

**`createNewChat`**:
- Calls `mockApi.sessions.create()` for a new session
- Prepends it to the sessions list
- Switches to the new session

**`addCustomModel`**:
- Calls `mockApi.models.add(label)` to persist the model
- Guards against duplicates (`prev.some(m => m.value === model.value)`)
- Appends and selects the new model

---

## `use-graph-ws.ts` — WebSocket Connection

### Purpose
Manages a single WebSocket connection to the LangGraph backend with auto-reconnect and a subscription-based event model.

### Exports

| Export | Type | Description |
|---|---|---|
| `GraphWsContext` | Context | React context for the WebSocket value |
| `useGraphWsProvider` | Hook | Creates the WebSocket context value |
| `useGraphWebSocket` | Hook | Consumes the WebSocket context |

### Context Value (`GraphWsContextValue`)

```typescript
interface GraphWsContextValue {
  connected: boolean;                                          // Connection state
  send: (action: string, payload?: Record<string, unknown>) => void;
  updateNodeState: (nodeId: string, state: Record<string, unknown>) => void;
  subscribe: (handler: WsMessageHandler) => () => void;        // Returns unsubscribe
  subscribeNodeState: (handler: NodeStateUpdateHandler) => () => void;
}
```

### Connection Lifecycle

```
1. connect() called on mount
2. Create new WebSocket(WS_URL)
3. onopen: set connected=true, reset reconnect delay
4. onmessage: parse JSON, dispatch to handlers by type:
   - "graph_data" → graphHandlers
   - "node_state_update" → nodeStateHandlers
   - "status" → toast.info
   - "error" → toast.error
5. onerror: set connected=false
6. onclose: set connected=false, schedule reconnect
7. Unmount: set intentionalClose flag, clear timers, close socket
```

### Reconnection Logic

- **Initial delay**: 2000ms
- **Backoff multiplier**: 1.5x per attempt
- **Maximum delay**: 30000ms (30s)
- **Reset**: On successful connection, delay returns to 2000ms
- **Prevention**: If `intentionalCloseRef.current` is true (component unmount), reconnection is skipped

### Handler Subscription

Uses `Set<WsMessageHandler>` and `Set<NodeStateUpdateHandler>` stored in refs:
- `subscribe(handler)` — Adds to set, returns `() => handlers.delete(handler)`
- `subscribeNodeState(handler)` — Same pattern for node state updates

### Error Handling

- Parse errors in `onmessage` are caught and logged to `console.warn`
- Errors sending messages: `toast.error("WebSocket not connected")` if socket is not OPEN

---

## `use-theme.ts` — Theme Management

### Purpose
Manages light/dark/system theme modes with persistence to localStorage.

### Exports

```typescript
function useTheme(): {
  theme: "light" | "dark" | "system";   // Current mode
  resolved: "light" | "dark";           // Actual applied theme
  cycle: () => void;                     // Cycle: system → light → dark → system
}
```

### Implementation

- **Initialization**: Reads from `localStorage.getItem("theme")`, defaults to `"system"`
- **Application**: Toggles `document.documentElement.classList.toggle("dark", ...)` based on resolved theme
- **System listener**: When in `"system"` mode, listens for `matchMedia("(prefers-color-scheme: dark)")` changes
- **Persistence**: Writes to `localStorage.setItem("theme", theme)` on every change

---

## `use-mobile.tsx` — Responsive Detection

### Purpose
Detects mobile viewport width for responsive UI adjustments.

### Exports

```typescript
function useIsMobile(): boolean;
```

### Implementation

- **Breakpoint**: 768px (`MOBILE_BREAKPOINT`)
- Uses `window.matchMedia("(max-width: 767px)")` for reactive updates
- Sets initial value from `window.innerWidth`

---

## `use-toast.ts` — Toast Notifications

### Purpose
shadcn/ui's toast notification system using a reducer pattern.

### Exports

| Export | Type | Description |
|---|---|---|
| `useToast` | Hook | Returns current toasts + `toast()` + `dismiss()` |
| `toast` | Function | Creates a new toast notification |

### Implementation

- **Limits**: `TOAST_LIMIT=1` (only one toast visible at a time)
- **Auto-remove delay**: `TOAST_REMOVE_DELAY=1000000ms` (essentially manual dismiss)
- **Reducer actions**: `ADD_TOAST`, `UPDATE_TOAST`, `DISMISS_TOAST`, `REMOVE_TOAST`
- **Listener pattern**: External `listeners` array updated via `useEffect`

### Usage

```typescript
import { toast } from "sonner";  // Preferred in this project

// Or from shadcn:
import { useToast } from "@/hooks/use-toast";
const { toast } = useToast();
toast({ title: "Error", description: "Something went wrong" });
```

Note: The project primarily uses `sonner` (imported from `import { toast } from "sonner"`) for toasts in graph and chat components, while the shadcn `use-toast` hook is available as an alternative.
