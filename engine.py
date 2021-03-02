from typing import Iterable, Any

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

class Engine:
    def __init__(self, event_handler: EventHandler, game_map: GameMap, player: Entity):
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player
        self.update_fov()
    
    def handle_events(self, events: Iterable[Any]) -> None:
        for event in events:
            action = self.event_handler.dispatch(event)

            if action is None:
                continue

            action.perform(self, self.player)

            self.update_fov() # 다음 행동 전에 시야 업데이트 

    def update_fov(self) -> None:
        """시야 범위를 플레이어의 시야에 맞게 업데이트"""
        self.game_map.visible[:] = compute_fov(self.game_map.tiles["transparent"], (self.player.x, self.player.y), radius=8,)
        #만약 타일이 "visible"이면 "explored"도 추가
        self.game_map.explored |= self.game_map.visible

    def render(self, console:Console, context:Context):
        self.game_map.render(console)

        context.present(console)

        console.clear()