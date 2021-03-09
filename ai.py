from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

import numpy as np
import tcod

from actions import Action, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from entity import Actor


class BaseAI(Action):
    entity:Actor

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x:int, dest_y:int) -> List[Tuple[int,int]]:
        """
            목표 위치로의 경로를 계산하고 리턴

            유효한 길이 없으면 빈 리스트를 반환
        """
        # copy the walkable array
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # 엔티티가 경로를 막고, 코스트가 0이 아닐경우(막힘)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # 막힌 경로에 cost 추가
                # 낮은 숫자는 더 많은 적으로 둘러쌓일 걸을 의미.
                # 높은 숫자는 적들이 플레이어를 감싸기까지 오래 걸릴것을 의미.
                cost[entity.x, entity.y] += 10

        # cost 배열로 그래프 생성, pathfinder는 그래프를 통해 길을 찾는다.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y)) #시작위치

        # 목적지까지의 경로를 계산하고 시작지점 삭제
        path: List[List[int]] = pathfinder.path_to((dest_x,dest_y))[1:].tolist()

        # List[List[int]]를 List[Tuple[int,int]]로 변환
        return [(index[0],index[1]) for index in path]

class HostileEnemy(BaseAI):
    def __init__(self, entity:Actor):
        super().__init__(entity)
        self.path: List[Tuple[int,int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx),abs(dy)) #chebyshev 거리

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(self.entity, dest_x - self.entity.x, dest.y - self.entity.y,).perform()

        return WaitAction(self.entity).perform()