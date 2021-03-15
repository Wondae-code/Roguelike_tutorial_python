from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from game_map import GameMap

T = TypeVar("T", bound="Entity")  # 나중에 문법 검색해보기


class Entity:
    """
    일반적인 오브젝트(플레이어, 적, 아이템 등등)
    """

    parent: Union[GameMap, Inventory]

    def __init__(
        self, parent: Optional[GameMap] = None, x: int = 0, y: int = 0,
        char: str = "?", color: Tuple[int, int, int] = [255, 255, 255],
        name: str = "<Unnamed>", blocks_movement: bool = False, render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        if parent:
            # 만약 parent가 없다면 나중에 초기화함.
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """주어진 위치에 인스턴스의 복제를 배치"""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """엔티티를 새로운 장소에 배치, GameMaps에서 움직임.(Handles moving across GameMaps?)"""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):
                self.parent.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """현재 엔티티와 주어진 좌표간의 거리를 리턴."""
        return math.sqrt((x - self.x)**2 + (y - self.y)**2)

    def move(self, dx=int, dy=int) -> None:
        # 엔티티를 주어진 양만큼 움직임
        self.x += dx
        self.y += dy


class Actor(Entity):
    def __init__(
        self, *, x: int = 0, y: int = 0, char: str = "?", color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>", ai_cls: Type[BaseAI], fighter: Fighter, inventory: Inventory,
    ):
        super().__init__(x=x, y=y, char=char, color=color, name=name,
                         blocks_movement=True, render_order=RenderOrder.ACTOR)

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

    @property
    def is_alive(self) -> bool:
        """행동을 취할 수 있는 한 True를 리턴"""
        return bool(self.ai)


class Item(Entity):
    def __init__(self, *, x: int = 0, y: int = 0, char: str = "?", color: Tuple[int, int, int] = (255, 255, 255), name: str = "<Unnamed>", consumable: Consumable,):
        super().__init__(x=x, y=y, char=char, color=color, name=name,
                         blocks_movement=False, render_order=RenderOrder.ITEM,)

        self.ai_cls = None
        self.consumable = consumable
        self.consumable.parent = self
