from __future__ import annotations

import copy
from typing import Optional, Tuple, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from game_map import GameMap

T = TypeVar("T", bound="Entity") #나중에 문법 검색해보기

class Entity:
    """
    일반적인 오브젝트(플레이어, 적, 아이템 등등)
    """

    gamemap: GameMap

    def __init__(self, gamemap:Optional[GameMap] = None, x:int = 0, y:int = 0, char:str = "?", color:Tuple[int,int,int] = [255,255,255], name:str = "<Unnamed>", blocks_movement:bool = False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        if gamemap:
            # 만약 Gamemap이 없다면 나중에 초기화함.
            self.gamemap = gamemap
            gamemap.entities.add(self)

    def spawn(self:T, gamemap:GameMap, x:int, y:int) -> T:
        """주어진 위치에 인스턴스의 복제를 배치"""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.gamemap = gamemap
        gamemap.entities.add(clone)
        return clone

    def place(self, x:int, y:int, gamemap: Optional[GameMap] = None) -> None:
        """엔티티를 새로운 장소에 배치, GameMaps에서 움직임.(Handles moving across GameMaps?)"""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "gamemap"):
                self.gamemap.entities.remove(self)
            self.gamemap = gamemap
            gamemap.entities.add(self)

        
    def move(self, dx=int, dy=int) -> None:
        #엔티티를 주어진 양만큼 움직임
        self.x += dx
        self.y += dy
