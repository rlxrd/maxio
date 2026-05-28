from __future__ import annotations


class State:
    """Одно состояние FSM. Ключ присваивается автоматически через __set_name__."""

    key: str

    def __set_name__(self, owner: type, name: str) -> None:
        self.key = f"{owner.__name__}:{name}"

    def __repr__(self) -> str:
        return f"<State {self.key!r}>"


class StatesGroup:
    """Группа состояний — пространство имён. State.__set_name__ делает всё сам."""
