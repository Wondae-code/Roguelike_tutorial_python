"""로딩과 게임 세션의 초기화를 관리"""
from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from typing import Optional

import tcod

import color
from engine import Engine
import entity_factories
from game_map import GameWorld
import input_handlers


# 배경 파일을 로드하고, 알파채널을 삭제한다.
background_image = tcod.image.load("menu_background.png")[:, :, :3]


def new_game() -> Engine:
    """새로운 game session을 엔진 instance로 리턴."""
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    max_monsters_per_room = 2
    max_items_per_room = 2

    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)

    engine.game_world = GameWorld(max_rooms=max_rooms, room_min_size=room_min_size,
                                       room_max_size=room_max_size, map_width=map_width, map_height=map_height,
                                       max_monsters_per_room=max_monsters_per_room, max_items_per_room=max_items_per_room, engine=engine)

    engine.game_world.generate_floor()
    engine.update_fov()

    engine.message_log.add_message(
        "Hello and welcome to yet another dungeon!", color.welcome_text)
    return engine


def load_game(filename: str) -> Engine:
    """파일에서 Engine instance를 로드."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine


class MainMenu(input_handlers.BaseEventHandler):
    """메인메뉴 render와 input을 관리."""

    def on_render(self, console: tcod.Console) -> None:
        """메인메뉴를 배경 이미지 위에 그린다"""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(console.width // 2, console.height // 2 - 4,
                      "TOMBS OF ANCIENT KINGS", fg=color.menu_title, alignment=tcod.CENTER,)
        console.print(console.width // 2, console.height - 2,
                      "By Wondae", fg=color.menu_title, alignment=tcod.CENTER,)

        menu_width = 24
        for i, text in enumerate(
            ["[N] Play a New Game", "[C] Continue Last Game", "[Q] Quit"]
        ):
            console.print(
                console.width // 2, console.height // 2 - 2 + i, text.ljust(menu_width), fg=color.menu_text, bg=color.black, alignment=tcod.CENTER, bg_blend=tcod.BKGND_ALPHA(64)
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.K_c:
            try:
                return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()
                return input_handlers.PopupMessage(self, f"Failed to load save:\{exc}")
        elif event.sym == tcod.event.K_n:
            return input_handlers.MainGameEventHandler(new_game())

        return None
