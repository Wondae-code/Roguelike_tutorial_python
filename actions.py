from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity

class Action:
    def __init__(self, entity:Actor) -> None:
            super().__init__
            self.entity = entity
        
    @property
    def engine(self) -> Engine:
        """이 행동에 알맞은 엔진을 리턴함"""
        return self.entity.gamemap.engine

    def perform(self) -> None:

        """
        Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.
        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses
        """
        raise NotImplementedError()

class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()

class WaitAction(Action):
    def perform(self) -> None:
        pass

class ActionWithDirection(Action):
    def __init__(self, entity:Actor, dx:int, dy:int):
        super().__init__(entity)

        self.dx=dx
        self.dy=dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """행동의 목적지를 리턴."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """목적지를 막고있는 엔티티를 리턴"""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)
    
    @property
    def target_actor(self) -> Optional[Actor]:
        """행동의 목적지에 있는 Actor를 리턴"""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            return # 공격할 엔티티가 없음.

        damage = self.entity.fighter.power - target.fighter.defense
        
        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(f"{attack_desc} for {damage} hit points.", attack_color)
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(f"{attack_desc} but does no damage.", attack_color)


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return # 목적지가 경계 밖임

        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return # 목적지가 타일에 의해 막혀있음

        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return # 목적지가 엔티티에 의해 막혀있음

        self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()