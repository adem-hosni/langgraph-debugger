from fastapi import APIRouter
from typing import TypeAlias

from . import history, chat, graph

RouteEntry: TypeAlias = tuple[APIRouter, str]

routes: list[RouteEntry] = [
    (history.router, history.prefix),
    (chat.router, chat.prefix),
    (graph.router, graph.prefix),
]
