import tcod as libtcod

def main() -> None:
  screen_width = 80
  screen_height = 50

  tileset = libtcod.tileset.load_tilesheet("sprite.png", 32, 8, libtcod.tileset.CHARMAP_TCOD)

  with libtcod.context.new_terminal(screen_width, 
  screen_height, 
  tileset=tileset, title="Yet Another Roguelike Tutorial",
  vsync=True,
  ) as context:
    root_console = libtcod.Console(screen_width, screen_height, order="F")
    while True:
      root_console.print(x=1,y=1,string="@")

      context.present(root_console)

      for event in libtcod.event.wait():
        if event.type == "QUIT:
          raise SystemExit()

if __name__ == "__main__":
  main()