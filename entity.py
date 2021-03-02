from __future__ import annotations

import copy
from typing import Tuple, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from game_map import GameMap

T = TypeVar("T", bound="Entity") #나중에 문법 검색해보기

class Entity:
    """
    일반적인 오브젝트(플레이어, 적, 아이템 등등)
    """
    def __init__(self, x:int = 0, y:int = 0, char:str = "?", color:Tuple[int,int,int] = [255,255,255], name:str = "<Unnamed>", blocks_movement:bool = False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement

    def spawn(self:T, gamemap:GameMap, x:int, y:int) -> T:
        """주어진 위치에 인스턴스의 복제를 배치"""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        gamemap.entities.add(clone)
        return clone

        
    def move(self, dx=int, dy=int) -> None:
        #엔티티를 주어진 양만큼 움직임
        self.x += dx
        self.y += dy
