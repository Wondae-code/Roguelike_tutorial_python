from typing import Tuple

class Entity:
    """
    일반적인 오브젝트(플레이어, 적, 아이템 등등)
    """
    def __init__(self, x:int, y:int, char:str, color:Tuple[int,int,int]):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        
    def move(self, dx=int, dy=int) -> None:
        #엔티티를 주어진 양만큼 움직임
        self.x += dx
        self.y += dy
