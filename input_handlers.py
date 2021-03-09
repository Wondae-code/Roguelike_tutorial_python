from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import tcod

import actions
from actions import (Action, EscapeAction, BumpAction, WaitAction, PickupAction)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    #Arrow Keys
    tcod.event.K_UP:(0,-1),
    tcod.event.K_DOWN:(0,1),
    tcod.event.K_LEFT:(-1,0),
    tcod.event.K_RIGHT:(1,0),
    tcod.event.K_HOME:(-1,-1),
    tcod.event.K_END:(-1,1),
    tcod.event.K_PAGEUP:(1,-1),
    tcod.event.K_PAGEDOWN:(1,1),
    #Numpad Keys
    tcod.event.K_KP_1:(0,-1),
    tcod.event.K_KP_2:(0,1),
    tcod.event.K_KP_3:(-1,0),
    tcod.event.K_KP_4:(1,0),
    tcod.event.K_KP_6:(-1,-1),
    tcod.event.K_KP_7:(-1,1),
    tcod.event.K_KP_8:(1,-1),
    tcod.event.K_KP_9:(1,1),
    #Vi Keys
    tcod.event.K_h:(0,-1),
    tcod.event.K_j:(0,1),
    tcod.event.K_k:(-1,0),
    tcod.event.K_l:(1,0),
    tcod.event.K_y:(-1,-1),
    tcod.event.K_u:(-1,1),
    tcod.event.K_b:(1,-1),
    tcod.event.K_n:(1,1),
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

class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine:Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> None:
        self.handle_action(self.dispatch(event))

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
            return False # 예외일 때, 적 턴 스킵

        self.engine.handle_enemy_turns()
        
        self.engine.update_fov()
        return True
    
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y
    
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

    def on_render(self, console:tcod.Console) -> None:
        self.engine.render(console)

class AskUserEventHandler(EventHandler):
    """특별한 입력을 요구하는 사용자 입력을 관리"""

    def handle_action(self, action:Optional[Action]) -> bool:
        """유효한 액션이 실행 됐을 때 main event handler로 돌아간다."""
        if super().handle_action(action):
            self.engine.event_handler = MainGameEventHandler(self.engine)
            return True
        return False
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
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

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        """디폴트로는 아무 마우스 클릭도 이 input handler를 나간다."""
        return self.on_exit()

    def on_exit(self) -> Optional[Action]:
        """유저가 나가길 시도하거나 action을 취소할때 호출된다.
        디폴트로는 main event handler로 돌아간다."""
        self.engine.event_handler = MainGameEventHandler(self.engine)
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
            x=40
        else:
            x=0
        
        y=0

        width = len(self.TITLE) + 4

        console.draw_frame(x=x, y=y, width=width, height=height, title=self.TITLE, clear=True, fg=(255,255,255), bg=(0,0,0),)

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                console.print(x+1, y+i+1, f"({item_key}) ({item.name})")
        else:
            console.print(x+2, y+1, "(Empty")

    def ev_keydown(self, event:tcod.event.KeyDown) -> Optional[Action]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(Self, item:Item) -> Optional[Action]:
        """유저가 유효한 아이템을 골랐을 때 호출된다."""
        raise NotImplementedError()

class InventoryActivateHandler(InventoryEventHandler):
    """인벤토리 아이템을 쓰는것을 관리"""
    TITLE ="Select an item to use"

    def on_item_selected(self, item:Item) -> Optional[Action]:
        """선택된 아이템에 대한 액션을 리턴한다."""
        return item.consumable.get_action(self.engine.player)

class InventoryDropHandler(InventoryEventHandler):
    """인벤토리 아이템을 떨어트리는 것을 관리"""
    TITLE = "Select an item to drop"

    def on_item_selected(self, item:Item) -> Optional[Action]:
        """이 아이템을 떨어트린다"""
        return actions.DropItem(self.engine.player, item)



class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None
        key = event.sym

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction(player)
        elif key == tcod.event.K_v:
            self.engine.event_handler = HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        elif key == tcod.event.K_i:
            self.engine.event_handler = InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            self.engine.event_handler = InventoryDropHandler(self.engine)

        return action

class GameOverEventHandler(EventHandler): 
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            raise SystemExit()

        #유효하지 않은 키가 눌릴 경우
        return action

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}

class HistoryViewer(EventHandler):
    """조종 가능한 큰 창에 히스토리를 출력"""

    def __init__(self, engine:Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console) # Draw the main state as the background

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(0, 0, log_console.width, 1, "-|Message history|-", alignment=tcod.CENTER)

        # 커서 파라메터를 이용해 메세지 로그를 그림
        self.engine.message_log.render_messages(log_console, 1,1, log_console.width - 2, log_console.height - 2, self.engine.message_log.messages[: self.cursor + 1],)
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
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
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0 # 바로 맨 위로 이동
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length -1 # 바로 맨 끝으로 이동
        else: # 다른 키는 메인 게임 화면으로 이동
            self.engine.event_handler = MainGameEventHandler(self.engine)