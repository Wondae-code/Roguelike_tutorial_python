from __future__ import annotations

import random
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],
    2: [(entity_factories.confusion_scroll, 10)],
    4: [(entity_factories.lighting_scroll, 25), (entity_factories.sword, 5)],
    6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],
    2: [(entity_factories.troll, 15)],
    4: [(entity_factories.troll, 30)],
    6: [(entity_factories.troll, 60)],
}

def get_max_value_for_floor(weighted_chances_by_floor: List[Tuple[int, int]], floor: int) -> int:
    current_value = 0

    for floor_minimum, value in weighted_chances_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value

def get_entities_at_random(weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]], number_of_entities: int, floor: int,) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]
                
                entity_weighted_chances[entity] = weighted_chance
        
    entities = list(entity_weighted_chances.keys())
    entity_weighted_chances_values = list(entity_weighted_chances.values())
    
    chosen_entities = random.choices(entities, weights=entity_weighted_chances_values, k = number_of_entities)

    return chosen_entities

class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """방의 내부를 2차원 어레이 인덱스로 리턴."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """이 방이 다른 방과 겹칠 경우 True를 리턴"""
        return(
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int,) -> None:
    number_of_monsters = random.randint(0, get_max_value_for_floor(max_monsters_by_floor, floor_number))
    number_of_items = random.randint(0, get_max_value_for_floor(max_items_by_floor, floor_number))

    monsters: List[Entity] = get_entities_at_random(enemy_chances, number_of_monsters, floor_number)
    items: List[Entity] = get_entities_at_random(item_chances, number_of_items, floor_number)

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)

def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """두 점 사이에 L모양의 통로를 리턴."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% 확률
        # 가로-세로 순서
        corner_x, corner_y = x2, y1
    else:
        # 세로-가로 순서
        corner_x, corner_y = x1, y2

    # 터널의 좌표 생성
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(max_rooms: int, room_min_size: int, room_max_size: int, map_width: int, map_height: int, engine: Engine,) -> GameMap:
    """새로운 던전 맵을 생성"""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom"가 사각형을 다루기 쉽게 함.
        new_room = RectangularRoom(x, y, room_width, room_height)

        # 다른 방과 교차하는지 확인.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # 겹치면 새로 만듬.
        # 교차하지 않으면 방은 유효함.

        # 방 대부를 파냄
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # 플레이어가 시작할 첫번째 방
            player.place(*new_room.center, dungeon)
        else:
            # 이전 방과 터널로 연결
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        dungeon.tiles[center_of_last_room] = tile_types.down_stairs
        dungeon.downstairs_location = center_of_last_room

        # 새로운 방을 목록에 추가
        rooms.append(new_room)

    return dungeon
