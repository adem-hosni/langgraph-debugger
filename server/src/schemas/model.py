from pydantic import BaseModel


class AIModel(BaseModel):
    label: str
    value: str
    custom: bool = False
