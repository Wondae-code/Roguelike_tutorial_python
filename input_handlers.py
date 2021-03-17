from __future__ import annotations

import os

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import tcod

import actions
from actions import (Action, BumpAction, WaitAction, PickupAction)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    # Arrow Keys
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad Keys
    tcod.event.K_KP_1: (0, -1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (-1, 0),
    tcod.event.K_KP_4: (1, 0),
    tcod.event.K_KP_6: (-1, -1),
    tcod.event.K_KP_7: (-1, 1),
    tcod.event.K_KP_8: (1, -1),
    tcod.event.K_KP_9: (1, 1),
    # Vi Keys
    tcod.event.K_h: (0, -1),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (-1, 0),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (-1, 1),
    tcod.event.K_b: (1, -1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""
active Event handler를 바꾸거나 action을 실행하는 트리거를 리턴하는 event handler.

만약 handler가 리턴되면 미래의 event를 위한 active handler가 됨.
만약 action이 리턴되면 액션이 실행되고, 유효한 것이면 MainGameEventHandler가 active handler가 된다.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """event를 관리하고, 다음 active event handler를 리턴."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(
            state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class PopupMessage(BaseEventHandler):
    """팝업 텍스트 윈도우를 띄움"""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_gandler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """parent와 dim(?)을 결과로 그리고, 그 다음 메세지를 위에 띄운다."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(console.width // 2, console.height // 2, self.text,
                      fg=color.white, bg=color.black, alignment=tcod.CENTER,)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """아무키 입력시 parent handler로 돌아간다."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """엔진에 관한 InputHandler를 위한 event를 관리."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # 유효한 action이 수행될 경우
            if not self.engine.player.is_alive:
                # 플레이어가 action 동안이나 이후에 죽었을 경우
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)

            return MainGameEventHandler(self.engine)
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """
        이벤트 메소드에서 리턴되는 actions을 관리,

        action이 턴을 진행시킬 경우 True를 리턴.
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # 예외일 때, 적 턴 스킵

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


class AskUserEventHandler(EventHandler):
    """특별한 입력을 요구하는 사용자 입력을 관리"""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """디폴트로는 아무키를 누르면 이 input handler를 나간다."""
        if event.sym in {
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """디폴트로는 아무 마우스 클릭도 이 input handler를 나간다."""
        return self.on_exit()

    def on_exit(self) -> Optional[Action]:
        """유저가 나가길 시도하거나 action을 취소할때 호출된다.
        디폴트로는 main event handler로 돌아간다."""
        return MainGameEventHandler(self.engine)

class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console:tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x=40
        else:
            x=0
        
        y = 0

        width = len(self.TITLE) + 4
        
        console.draw_frame(x=x, y=y, width=width, height=7, title=self.TITLE, clear=True, fg=(255, 255, 255), bg=(0, 0, 0),)
        
        console.print(x=x+1, y=1, string=f"Level: {self.engine.player.level.current_level}")
        console.print(x=x+1, y=2, string=f"XP: {self.engine.player.level.current_xp}")
        console.print(x=x+1, y=3, string=f"XP for next level: {self.engine.player.level.experience_to_next_level}")
        console.print(x=x+1, y=4, string=f"Attack: {self.engine.player.fighter.power}")
        console.print(x=x+1, y=5, string=f"Defense: {self.engine.player.fighter.defense}")

class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console:tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(x=x, y=0, width=35, height=8, title=self.TITLE, clear=True, fg=(255, 255, 255), bg=(0, 0, 0),)

        console.print(x=x+1, y=1, string="Congratulations! You Level up!")
        console.print(x=x+1, y=2, string="Select an attribute to increase.")

        console.print(x=x+1, y=4, string=f"a) constitution (+20HP, from {self.engine.player.fighter.max_hp})",)
        console.print(x=x+1, y=5, string=f"b) strength (+1 atk, from {self.engine.player.fighter.power})",)
        console.print(x=x+1, y=6, string=f"c) defense (+1 def, from {self.engine.player.fighter.defense})")

    def ev_keydown(self, event = tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            if index == 1:
                player.level.increase_power()
            if index == 2:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event:tcod.evnet.MouseButtonDown) -> Optional[ActionOrHandler]:
        """보통처럼 플레이어가 클릭을 통해 나가지 않도록 한다."""
        return None


class InventoryEventHandler(AskUserEventHandler):
    """이 handler는 유저가 아이템을 고를 수 있게 한다. 그 뒤 이러나는 일은 subclass를 따른다."""

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> none:
        """인벤토리 속 아이템과 선택할 글자를 표현하는 메뉴를 그린다.
        플레이어의 위치에 따라 다른 곳으로 이동하여 플레이어가 어디에 있던 메뉴를 볼 수 있게 한다."""
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(x=x, y=y, width=width, height=height,
                           title=self.TITLE, clear=True, fg=(255, 255, 255), bg=(0, 0, 0),)

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                console.print(x+1, y+i+1, f"({item_key}) ({item.name})")
        else:
            console.print(x+2, y+1, "(Empty")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message(
                    "Invalid entry", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(Self, item: Item) -> Optional[ActionOrHandler]:
        """유저가 유효한 아이템을 골랐을 때 호출된다."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """인벤토리 아이템을 쓰는것을 관리"""
    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """선택된 아이템에 대한 액션을 리턴한다."""
        return item.consumable.get_action(self.engine.player)


class InventoryDropHandler(InventoryEventHandler):
    """인벤토리 아이템을 떨어트리는 것을 관리"""
    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """이 아이템을 떨어트린다"""
        return actions.DropItem(self.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    def __init__(self, engine: Engine):
        """이 관리자가 생성되면 커서를 플레이어 쪽으로 설정한다."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """타일 아래에 있는 커서를 타일 위로 강조한다."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """확인 키나 이동키를 체크한다"""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # modifier키를 누르면 키 이동을 빠르게 한다.
            if event.mod & tcod.event.KMOD_SHIFT:
                modifier *= 5
            if event.mod & tcod.event.KMOD_CTRL:
                modifier *= 10
            if event.mod & tcod.event.KMOD_ALT:
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # 커서의 크기를 맵 사이즈에 맞춘다.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """왼쪽 클릭으로 선택을 확인한다."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """인덱스가 선택 됐을 때 호출."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """플레이어가 키보드를 이용해 둘러볼수 있게 한다."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """MainHandler로 돌아간다."""
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """하나의 적을 가리키는 것을 관리. 선택된 적만 영향을 받는다."""

    def __init__(self, engine: Engine, callback: Callable[Tuple[int, int], Optional[Action]]):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """주어진 원호 안에 있는 적을 가리키는 것을 관리. 구역 안에 있는 엔티티는 영향을 받음."""

    def __init__(self, engine: Engine, radius: int, callback: Callable[Tuple[int, int], Optional[Action]],):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """커서 아래에 있는 타일 강조"""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # 목표지점 근처에 사각형을 그려서, 영향 받는 타일을 볼 수 있게 한다.
        console.draw_frame(x=x - self.radius - 1, y=y - self.radius - 1,
                           width=self.radius**2, height=self.radius**2, fg=color.red, clear=False,)

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None
        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & tcod.event.KMOD_SHIFT:
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)

        # 유효한 키가 아닐 때
        return action


class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """완료된 게임에서 나오는 것을 관리."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # 활성화된 저장 파일을 삭제.
        raise exceptions.QuitWithoutSaving()  # 완료된 게임을 저장하는 것을 피함.

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()


CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """조종 가능한 큰 창에 히스토리를 출력"""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(0, 0, log_console.width, 1,
                              "-|Message history|-", alignment=tcod.CENTER)

        # 커서 파라메터를 이용해 메세지 로그를 그림
        self.engine.message_log.render_messages(
            log_console, 1, 1, log_console.width - 2, log_console.height - 2, self.engine.message_log.messages[: self.cursor + 1],)
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        # 멋진 조건부 이동을 추가
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # 위 끝에 있을 때, 아래로만 이동
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # 아래 끝에서 맨 첫번째로 이동
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log (해석 필요)
                self.cursor = max(
                    0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # 바로 맨 위로 이동
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # 바로 맨 끝으로 이동
        else:  # 다른 키는 메인 게임 화면으로 이동
            return MainGameEventHandler(self.engine)
        return None
