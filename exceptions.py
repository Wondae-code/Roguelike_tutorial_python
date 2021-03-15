class Impossible(Exception):
    """
    불가능한 행동을 실행할 때 예외 발생.

    이유는 예외 메세지에 주어짐.
    """


class QuitWithoutSaving(SystemExit):
    """자동 저장 없이 게임이 종료될 때 호출."""
