# Pydantic Schemas Reference

This document describes all Pydantic models used for request/response serialization and type validation.

---

## CamelCase Configuration

Most schemas inherit from `CamelBaseModel` which configures Pydantic to:

- **Accept** both `snake_case` and `camelCase` input (via `populate_by_name=True`)
- **Output** `camelCase` JSON (via `alias_generator=to_camel`)
- **Read** from ORM attributes (via `from_attributes=True`)

```python
class CamelBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
```

---

## Chat Schemas (`server/src/schemas/chat.py`)

### Type Aliases

| Alias | Values |
|---|---|
| `ChatModeType` | `"default"`, `"thinking"`, `"research"`, `"creative"`, `"concise"` |
| `AttachmentType` | `"code"`, `"data"`, `"image"`, `"document"` |
| `ToolIconType` | `"globe"`, `"code"`, `"database"`, `"search"` |
| `ToolStatusType` | `"completed"`, `"running"`, `"error"` |
| `RoleType` | `"user"`, `"assistant"` |

### Attachment

```python
class Attachment(CamelBaseModel):
    name: str
    type: AttachmentType
    size: str | None = None
```

### ToolCall

```python
class ToolCall(CamelBaseModel):
    name: str
    icon: ToolIconType
    status: ToolStatusType
    input: dict[str, Any]
    output: dict[str, Any]
```

### ChatMessage

```python
class ChatMessage(CamelBaseModel):
    id: str
    role: RoleType
    content: str
    attachments: list[Attachment] | None = None
    thinking: str | None = None
    toolCalls: list[ToolCall] | None = None  # serializes as "toolCalls"
    timestamp: str
```

### ChatSession

```python
class ChatSession(CamelBaseModel):
    id: str
    title: str
    date: str
    messages: list[ChatMessage]
```

### AIModel

```python
class AIModel(CamelBaseModel):
    value: str
    label: str
    custom: bool | None = None
```

### ChatModeInfo

```python
class ChatModeInfo(CamelBaseModel):
    value: ChatModeType
    label: str
    description: str
```

### SendMessageRequest

```python
class SendMessageRequest(CamelBaseModel):
    sessionId: str
    content: str
    attachments: list[Attachment] | None = None
    model_name: str = Field(alias="model")  # accepts "model", outputs "modelName"
    mode: ChatModeType
```

### SendMessageResponse

```python
class SendMessageResponse(CamelBaseModel):
    userMessage: ChatMessage
    assistantMessage: ChatMessage
    updatedSessionTitle: str | None = None
    # Note: serializes as "updatedSessionTitle" via CamelBaseModel
    # The route returns "updated_session_title" directly
```

### Constants

```python
CHAT_MODES: list[ChatModeInfo] = [
    ChatModeInfo(value="default",    label="Default",       description="Balanced responses"),
    ChatModeInfo(value="thinking",   label="Deep Thinking",  description="Step-by-step reasoning"),
    ChatModeInfo(value="research",   label="Research",       description="In-depth analysis with sources"),
    ChatModeInfo(value="creative",   label="Creative",       description="Imaginative and expressive"),
    ChatModeInfo(value="concise",    label="Concise",        description="Brief and to the point"),
]

DEFAULT_MODELS: list[AIModel] = [
    AIModel(value="gpt-4o",          label="GPT-4o"),
    AIModel(value="claude-3.5-sonnet", label="Claude 3.5 Sonnet"),
    AIModel(value="gemini-1.5-pro",  label="Gemini 1.5 Pro"),
    AIModel(value="gpt-4o-mini",     label="GPT-4o Mini"),
]
```

---

## Graph Schemas (`server/src/schemas/graph.py`)

### Type Aliases

| Alias | Values |
|---|---|
| `NodeStatusType` | `"idle"`, `"running"`, `"success"`, `"error"` |
| `GraphNodeType` | `"start"`, `"agent"`, `"tool"`, `"end"` |

### GraphNodeData

The custom data payload inside a React Flow node.

```python
class GraphNodeData(CamelBaseModel):
    label: str
    type: GraphNodeType
    status: NodeStatusType
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    state: dict[str, Any] | None = None
    error: str | None = None
    has_breakpoint: bool = False  # serializes as "hasBreakpoint"
```

### NodePosition

```python
class NodePosition(CamelBaseModel):
    x: float
    y: float
```

### NodeFlow

Maps to React Flow's `Node<GraphNodeData>` type.

```python
class NodeFlow(CamelBaseModel):
    id: str
    type: str  # "graphNode" for custom node rendering
    position: NodePosition
    data: GraphNodeData
```

### EdgeFlow

Maps to React Flow's `Edge` type.

```python
class EdgeFlow(CamelBaseModel):
    id: str
    source: str
    target: str
    animated: bool | None = None
    style: dict[str, Any] | None = None
```

### ExecutionStep

```python
class ExecutionStep(CamelBaseModel):
    node_id: str  # serializes as "nodeId"
    status: NodeStatusType
```

### GraphData

The master payload returned by the graph info endpoint.

```python
class GraphData(CamelBaseModel):
    nodes: list[NodeFlow]
    edges: list[EdgeFlow]
    execution_steps: list[ExecutionStep]  # serializes as "executionSteps"
```

---

## Model Schema (`server/src/schemas/model.py`)

```python
class AIModel(BaseModel):
    label: str
    value: str
    custom: bool = False
```

This is a standalone model (not inheriting `CamelBaseModel`) used for simple model data transfer.

---

## Client-Side Type Equivalents (`client/src/lib/mock-data.ts`)

The frontend defines matching TypeScript types:

```typescript
interface Attachment { name: string; type: "code" | "data" | "image" | "document"; size?: string; }
interface ToolCall { name: string; icon: "globe" | "code" | "database" | "search"; status: "completed" | "running" | "error"; input: Record<string, unknown>; output: Record<string, unknown>; }
interface ChatMessage { id: string; role: "user" | "assistant"; content: string; attachments?: Attachment[]; thinking?: string; toolCalls?: ToolCall[]; timestamp: string; }
interface ChatSession { id: string; title: string; date: string; messages: ChatMessage[]; }
interface AIModel { value: string; label: string; custom?: boolean; }
type ChatMode = "default" | "thinking" | "research" | "creative" | "concise";
```

And for graph data (`client/src/lib/graph-data.ts`):

```typescript
type NodeStatus = "idle" | "running" | "success" | "error";
interface GraphNodeData {
  label: string;
  type: "start" | "agent" | "tool" | "end";
  status: NodeStatus;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  state?: Record<string, unknown>;
  error?: string;
  hasBreakpoint?: boolean;
  onToggleBreakpoint?: (nodeId: string) => void;
  nodeId?: string;
}
```
