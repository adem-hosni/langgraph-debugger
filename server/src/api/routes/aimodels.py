import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from langgraph.graph.state import CompiledStateGraph

from db.session import get_db
from db.models import AIModel

router = APIRouter(tags=["AI Models"])
prefix = "/models"


@router.post("/add")
async def add_aimodel(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        model = AIModel(
            label=(await request.json()).get("label"),
            value=(await request.json()).get("label", "").replace("-", " ").title(),
            custom=True,
        )
        db.add(model)
        db.commit()
        return model.serialize(exclude_columns=["id"])
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fetch")
async def fetch_aimodels(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        stmt = select(AIModel)
        aimodels = db.scalars(stmt).all()
        return [aimodel.serialize(exclude_columns=["id"]) for aimodel in aimodels]
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{label}")
async def delete_aimodel(
    label: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        stmt = select(AIModel).where(AIModel.label == label)
        aimodel = db.scalars(stmt).first()
        if not aimodel:
            raise HTTPException(status_code=404, detail="Model not found")
        db.delete(aimodel)
        db.commit()
        return JSONResponse(content={"detail": "Model deleted"})
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
