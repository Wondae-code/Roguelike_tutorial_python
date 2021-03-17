from typing import Tuple

import numpy as np

# Console.tiles_rgb와 타일 그래픽구조를 맞추는 것,
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # 유니코드 코드포인트
        ("fg", "3B"),  # foreground color, RGB
        ("bg", "3B"),  # background color, RGB
    ]
)

# 정의된 타일 데이터를 타일 구조에 맞추는 것
tile_dt = np.dtype(
    [
        ("walkable", np.bool),
        ("transparent", np.bool),  # 시야를 가리지 않는 타일
        ("dark", graphic_dt),  # 시야에 없는 타일
        ("light", graphic_dt)  # 시야에 있는 타일
    ]
)


def new_tile(
    *,  # 파라메터의 순서가 상관 없게 하는 것
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """각각의 타일 타입을 정의 하는 것을 도우는 함수"""
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)


# SHROUD는 탐험되지 않고 보이지 않는 타일
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

floor = new_tile(
    walkable=True, transparent=True, dark=(ord(" "), (255, 255, 255), (50, 50, 150)), light=(ord(" "), (255, 255, 255), (200, 180, 50)),
)

wall = new_tile(
    walkable=False, transparent=False, dark=(ord(" "), (255, 255, 255), (0, 0, 100)), light=(ord(" "), (255, 255, 255), (130, 110, 50))
)

down_stairs = new_tile(
    walkable=True, transparent=True, dark=(ord(">"), (0,0,100), (50,50,150)), light=(ord(">"), (255,255,255),(200,180,50)),
)