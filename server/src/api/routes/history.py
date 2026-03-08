from sqlalchemy import select, desc
from sqlalchemy.orm import Session, selectinload

from fastapi import APIRouter, Depends, Request, HTTPException
from langgraph.graph.state import CompiledStateGraph

from db.models import HumanMessageRecord, SessionRecord
from db.session import get_db

# 1. Export the router and the prefix to match your RouteEntry format
router = APIRouter(tags=["Run History"])
prefix = "/history"


# Dependency to get the graph from app state
def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph


@router.get("/threads")
async def get_latest_state(
    db: Session = Depends(get_db), graph: CompiledStateGraph = Depends(get_graph)
):
    """
    Fetches only the most recent state for a thread.
    """
    # if not graph.checkpointer:
    #     raise HTTPException(status_code=400, detail="Checkpointer required.")

    try:
        stmt = (
            select(SessionRecord)
            .options(
                selectinload(SessionRecord.messages)
                .selectinload(HumanMessageRecord.response)
            )
            .order_by(desc(SessionRecord.date))
        )
        sessions = db.scalars(stmt).all()

        chats = []
        
        for session in sessions:
            formatted_messages = []
            
            for human_msg in session.messages:
                h_dict = human_msg.serialize(include_relationships=False)
                formatted_messages.append(human_msg.serialize(include_relationships=False))
                
                if human_msg.response:
                    ai_dict = human_msg.response.serialize(include_relationships=False)
                    ai_dict["role"] = "assistant"
                    
                    formatted_messages.append(ai_dict)

            chats.append({
                "id": str(session.id),
                "title": session.title,
                "date": session.date,
                "messages": formatted_messages,
            })

        return chats
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}")
async def get_thread_history(
    thread_id: str, graph: CompiledStateGraph = Depends(get_graph)
):
    """
    Retrieves the entire state history of a specific thread.
    Useful for visualizing past runs or rendering a timeline in the Lovable UI.
    """
    # History requires a checkpointer (like AsyncSqliteSaver or MemorySaver)
    if not graph.checkpointer and False:
        raise HTTPException(
            status_code=400,
            detail="The provided graph does not have a checkpointer configured. History is unavailable.",
        )

    config = {"configurable": {"thread_id": thread_id}}

    try:
        # get_state_history returns a generator of StateSnapshot objects
        history_generator = graph.get_state_history(config)

        history_data = []
        for state in history_generator:
            history_data.append(
                {
                    "checkpoint_id": state.config["configurable"]["checkpoint_id"],
                    "values": state.values,
                    "next": state.next,  # Which nodes were queued up next at this point in time
                    # 'created_at' might be available depending on your checkpointer version
                    "created_at": getattr(state, "created_at", None),
                }
            )

        return {
            "thread_id": thread_id,
            "total_checkpoints": len(history_data),
            "history": history_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}/latest")
async def get_latest_state(
    thread_id: str, graph: CompiledStateGraph = Depends(get_graph)
):
    """
    Fetches only the most recent state for a thread.
    """
    if not graph.checkpointer:
        raise HTTPException(status_code=400, detail="Checkpointer required.")

    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = graph.get_state(config)
        return {"thread_id": thread_id, "values": state.values, "next": state.next}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
