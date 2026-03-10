from fastapi import APIRouter
from typing import TypeAlias

from . import history, chat, graph, aimodels

RouteEntry: TypeAlias = tuple[APIRouter, str]

routes: list[RouteEntry] = [
    (history.router, history.prefix),
    (chat.router, chat.prefix),
    (graph.ws_router, graph.prefix),
    (aimodels.router, aimodels.prefix),
]
