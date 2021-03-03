from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import EventHandler

if TYPE_CHECKING:
    from entity import Entity
    from game_map import GameMap

class Engine:
    game_map:GameMap

    def __init__(self, player: Entity):
        self.event_handler:EventHandler = EventHandler(self)
        self.player = player

    def handle_enemy_turns(self) -> None:
        for entity in self.game_map.entities - {self.player}:
            print(f'The {entity.name} wonders when it will get to take a real turn.')

    def update_fov(self) -> None:
        """시야 범위를 플레이어의 시야에 맞게 업데이트"""
        self.game_map.visible[:] = compute_fov(self.game_map.tiles["transparent"], (self.player.x, self.player.y), radius=8,)
        #만약 타일이 "visible"이면 "explored"도 추가
        self.game_map.explored |= self.game_map.visible

    def render(self, console:Console, context:Context):
        self.game_map.render(console)

        context.present(console)

        console.clear()