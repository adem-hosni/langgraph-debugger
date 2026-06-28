# Database Schema

The server uses SQLite via SQLAlchemy 2.0 ORM. Tables are auto-created on startup via `Base.metadata.create_all(bind=engine)`.

**Source**: `server/src/db/models.py`

---

## Entity-Relationship Diagram

```
sessions
    │
    ├──< human_messages
    │       │
    │       ├──< attachments
    │       │
    │       └──> ai_messages
    │               │
    │               └──< tool_calls
    │
ai_models (independent)
```

---

## Tables

### `sessions`

Represents a chat conversation session.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | String(36) | PK, Index, default=uuid4 | Unique session identifier |
| `title` | String | NOT NULL | Session title (first 30 chars of first message) |
| `date` | String | NOT NULL | Date in `YYYY-MM-DD` format |

**Relationships**:
- `messages` → One-to-Many with `HumanMessageRecord` (cascade delete)

### `human_messages`

Stores user messages.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | String(36) | PK, Index, default=uuid4 | Unique message identifier |
| `session_id` | String(36) | FK → sessions.id, CASCADE | Parent session |
| `content` | Text | NOT NULL | Message text |
| `timestamp` | String | NOT NULL | Time in `HH:MM AM/PM` format |

**Relationships**:
- `session` → Many-to-One with `SessionRecord`
- `attachments` → One-to-Many with `AttachmentRecord` (cascade delete)
- `response` → One-to-One with `AIMessageRecord` (cascade delete, uselist=False)

### `ai_messages`

Stores AI assistant responses.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | String(36) | PK, Index, default=uuid4 | Unique message identifier |
| `human_message_id` | String(36) | FK → human_messages.id, CASCADE | Parent human message |
| `content` | Text | NOT NULL | AI response text |
| `thinking` | Text | NULLABLE | AI's step-by-step reasoning |
| `model` | String | NULLABLE | AI model used (e.g., "gpt-4o") |
| `mode` | String | NULLABLE | Chat mode (e.g., "default") |
| `timestamp` | String | NOT NULL | Time in `HH:MM AM/PM` format |

**Relationships**:
- `tool_calls` → One-to-Many with `ToolCallRecord` (cascade delete)
- `human_message` → Many-to-One with `HumanMessageRecord`

### `attachments`

Stores file attachments associated with human messages.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | Attachment identifier |
| `human_message_id` | String(36) | FK → human_messages.id, CASCADE | Parent message |
| `name` | String | NOT NULL | File name |
| `type` | String | NOT NULL | File type (code, data, image, document) |
| `size` | String | NULLABLE | Human-readable file size |

**Relationships**:
- `message` → Many-to-One with `HumanMessageRecord`

### `tool_calls`

Stores tool invocation records within AI responses.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | Tool call identifier |
| `ai_message_id` | String(36) | FK → ai_messages.id, CASCADE | Parent AI message |
| `name` | String | NOT NULL | Tool name (e.g., "Web Search") |
| `icon` | String | NOT NULL | Icon identifier (globe, code, database, search) |
| `status` | String | NOT NULL | Status (completed, running, error) |
| `input` | JSON | NOT NULL | Tool input parameters |
| `output` | JSON | NOT NULL | Tool output results |

**Relationships**:
- `ai_message` → Many-to-One with `AIMessageRecord`

### `ai_models`

Stores AI model configurations.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | Model identifier |
| `label` | String | NOT NULL | Display label (e.g., "GPT-4o") |
| `value` | String | NOT NULL | Model value identifier (e.g., "gpt-4o") |
| `custom` | Boolean | NOT NULL | Whether this is a user-added model |

---

## Serialization

The `Base` class provides a generic `serialize()` method:

```python
def serialize(self, include_relationships=True, exclude_columns=None):
```

- Iterates over all column attributes, excluding any in `exclude_columns`
- If `include_relationships` is True, recursively serializes relationships
- List relationships return arrays of serialized objects
- Scalar relationships return a single serialized object

### Overrides

**`AIMessageRecord.serialize()`** — Adds `"role": "assistant"` to the output.

**`HumanMessageRecord.serialize()`** — Adds `"role": "user"` to the output.

---

## Session Management

The `get_db()` dependency in `server/src/db/session.py` provides a per-request database session:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Database URL is configurable via `settings.SQLALCHEMY_DATABASE_URL` (default: `sqlite:///./database.db`). The engine uses `connect_args={"check_same_thread": False}` to allow SQLite access from multiple threads (required by FastAPI's async nature).
