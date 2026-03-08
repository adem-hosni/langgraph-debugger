import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from langgraph.graph.state import CompiledStateGraph

from db.session import get_db
from db.models import SessionRecord, HumanMessageRecord, AIMessageRecord
from schemas.chat import (
    SendMessageRequest,
    SendMessageResponse,
    ChatMessage,
)

router = APIRouter(tags=["Chat Execution"])
prefix = "/chat"


def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph


@router.post("/send", response_model=SendMessageResponse)
async def send_chat_message(
    req: SendMessageRequest,
    request: Request,
    db: Session = Depends(get_db),
    graph: CompiledStateGraph = Depends(get_graph),
):
    # 1. Prepare standard timestamps and IDs
    current_time = datetime.now().strftime("%I:%M %p")
    user_msg_id = str(uuid.uuid4())
    ai_msg_id = str(uuid.uuid4())

    # 2. Check if this is a new session in the Database
    db_session = (
        db.query(SessionRecord).filter(SessionRecord.id == req.sessionId).first()
    )
    updated_title = None

    if not db_session:
        # Create a new session if it doesn't exist
        updated_title = (
            req.content[:30] + "..." if len(req.content) > 30 else req.content
        )
        db_session = SessionRecord(
            title=updated_title,
            date=datetime.now().strftime("%Y-%m-%d"),
        )
        db.add(db_session)
        db.commit()

    # 3. Execute the LangGraph
    # We pass the sessionId as the thread_id so the graph's memory checkpointer tracks it
    config = {"configurable": {"thread_id": req.sessionId}}

    try:
        graph_input = {"input_text": req.content}

        # Invoke the graph asynchronously
        result_state = await graph.ainvoke(graph_input, config=config)

        # Extract the AI's response from the final state
        # NOTE: Adjust "result" to match the key your graph outputs
        ai_response_text = result_state.get(
            "result", "Execution complete, but no 'result' key found in state."
        )

    except Exception as e:
        print(f"Graph Execution Error: {e}")
        raise HTTPException(status_code=500, detail="Error executing AI Graph.")

    # 4. Save the Messages to the Database
    user_record = HumanMessageRecord(
        session_id=req.sessionId,
        content=req.content,
        timestamp=current_time,
    )
    db.add(user_record)
    db.commit()

    ai_record = AIMessageRecord(
        human_message_id=user_record.id,
        content=ai_response_text,
        timestamp=current_time,
        model=req.model_name,
        mode=req.mode,
    )
    db.add(ai_record)
    db.commit()

    # 5. Return the perfectly typed response to the frontend
    return SendMessageResponse(
        userMessage=ChatMessage(
            id=user_msg_id, role="user", content=req.content, timestamp=current_time
        ),
        assistantMessage=ChatMessage(
            id=ai_msg_id,
            role="assistant",
            content=ai_response_text,
            timestamp=current_time,
        ),
        updated_session_title=updated_title,
    )
