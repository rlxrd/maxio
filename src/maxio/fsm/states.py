from __future__ import annotations


class State:
    """A single FSM state. The key is assigned automatically via ``__set_name__``."""

    key: str

    def __set_name__(self, owner: type, name: str) -> None:
        self.key = f"{owner.__name__}:{name}"

    def __repr__(self) -> str:
        return f"<State {self.key!r}>"


class StatesGroup:
    """Namespace for a group of related FSM states.

    Example:
        ```python
        class Form(StatesGroup):
            name = State()
            age  = State()
        ```
    """
