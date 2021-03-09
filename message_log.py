from typing import Iterable, List, Reversible, Tuple
import textwrap

import tcod

import color

class Message:
    def __init__(self, text:str, fg: Tuple[int, int, int]):
        self.plain_text = text
        self.fg = fg
        self.count = 1

    @property
    def full_text(self) -> str:
        """메세지의 전체 내용, 필요할 경우 카운트"""
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        return self.plain_text

class MessageLog:
    def __init__(self) -> None:
        self.messages: List[Message] = []

    def add_message(self, text: str, fg: Tuple[int, int, int] = color.white, *, stack: bool = True,) -> None:
        """
        로그에 메세지 추가, `text`는 메세지, `fg`는 텍스트 컬러.
        만약 `stack`이 True면 매세지는 이전 메세지와 같은 텍스트에 쌓임.
        """
        if stack and self.messages and text == self.messages[-1].plain_text:
            self.messages[-1].count += 1
        else:
            self.messages.append(Message(text,fg))
    
    def render(self, console: tcod.Console, x:int, y:int, width:int, height:int,) -> None:
        """주어진 장소에 로그를 그림."""
        self.render_messages(console, x, y, width, height, self.messages)

    @staticmethod
    def wrap(string: str, width:int) -> Iterable[str]:
        """wrap된 텍스트 메세지를 출력"""
        for line in string.splitlines(): # 메세지의 새로운 줄 관리
            yield from textwrap.wrap(line, width, expand_tabs=True,)

    @classmethod
    def render_messages(cls, console:tcod.Console, x:int, y:int, width:int, height:int, messages:Reversible[Message],) -> None:
        """
        제공된 메세지를 그림.
        `messages`는 끝에서 시작하여 거꾸로 그려짐.
        """
        y_offset = height - 1
        for message in reversed(messages):
            for line in reversed(list(cls.wrap(message.full_text, width))):
                console.print(x=x, y=y + y_offset, string=line, fg=message.fg)
                y_offset -= 1
                if y_offset < 0:
                    return #메세지를 출력 할 공간이 없음.