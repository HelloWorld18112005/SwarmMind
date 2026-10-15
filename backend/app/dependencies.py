from typing import Annotated
from fastapi import Depends

from app.config import Settings, get_settings
from app.graph.base import GraphRepository
from app.graph.factory import get_graph_repository


async def get_repository() -> GraphRepository:
    return await get_graph_repository()


SettingsDep = Annotated[Settings, Depends(get_settings)]
GraphRepoDep = Annotated[GraphRepository, Depends(get_repository)]
