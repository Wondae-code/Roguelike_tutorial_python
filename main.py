import traceback

import tcod

import color
import exceptions
import input_handlers
import setup_game

def save_game(handler: input_handlers.BaseEventHandler, filename:str) -> None:
    """만약 현재 event handler가 active Engine을 가지고 있다면 저장한다."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")


def main() -> None:
    screen_width = 80
    screen_height = 50
    
    tileset = tcod.tileset.load_tilesheet("sprite.png", 32, 8, tcod.tileset.CHARMAP_TCOD)

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    with tcod.context.new_terminal(screen_width,
                                   screen_height,
                                   tileset=tileset, title="Yet Another Roguelike Tutorial",
                                   vsync=True,
                                   ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # 예외 관리
                    traceback.print_exc()  # stderr에 출력
                    # message_log에도 출력
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error)
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # 저장 후 종료
            save_game(handler, "savegame.sav")
            raise
        except BaseException:  # 다른 예상못한 예외에도 저장
            save_game(handler, "savegame.sav")
            raise


if __name__ == "__main__":
    main()
