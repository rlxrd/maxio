from __future__ import annotations

from maxio.fsm.context import current_fsm_context
from maxio.fsm.states import State
from maxio.types.update import Update


class StateFilter:
    """Passes an update only when the user's current FSM state matches one of the given states."""

    def __init__(self, *states: State | str) -> None:
        self.states = {s.key if isinstance(s, State) else s for s in states}

    async def check(self, update: Update) -> bool:
        ctx = current_fsm_context.get()
        if ctx is None:
            return False
        current = await ctx.get_state()
        return current in self.states
