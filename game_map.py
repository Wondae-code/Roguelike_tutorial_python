from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING

import numpy as np
from tcod.console import Console

import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    def __init__(self, engine:Engine, width:int, height:int, entities: Iterable[Entity] = ()):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width,height), fill_value=tile_types.wall, order="F")

        self.visible = np.full((width, height), fill_value=False, order="F") #플레이어가 현재 볼 수 있는 타일
        self.explored = np.full((width, height), fill_value=False, order="F") #플레이어가 봤었던 타일

    def get_blocking_entity_at_location(self, location_x:int, location_y:int,) -> Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity
        
        return None

    def in_bounds(self, x:int, y:int) -> bool:
        """만약 x와 y가 맵의 경계 안이면 True를 출력"""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console:Console) -> None:
        """
        맵을 그림.

        만약 타일이 "visible"면 "light"로 그림, "visible"이 아니고 "Explored"상태면 "dark로 표시, 디폴트는 "SHROUD"
        """
        console.tiles_rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )
        
        for entity in self.entities:
            #시야 내의 엔티티만 표현
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)
