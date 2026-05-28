from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from maxio.types.update import Update

# Фильтр — это либо объект с методом check, либо простой callable(Update) -> bool.
FilterFunc = Callable[[Update], bool | Awaitable[bool]]


@runtime_checkable
class Filter(Protocol):
    async def check(self, update: Update) -> bool: ...


async def apply_filter(flt: Filter | FilterFunc, update: Update) -> bool:
    if isinstance(flt, Filter):
        return await flt.check(update)
    result = flt(update)
    if inspect.isawaitable(result):
        return await result
    return bool(result)


class Command:
    """Совпадает, если текст сообщения начинается с одной из команд (например `/start`)."""

    def __init__(self, *commands: str, prefix: str = "/") -> None:
        self.prefix = prefix
        self.commands = {c.lstrip(prefix) for c in commands}

    async def check(self, update: Update) -> bool:
        text = update.message.text if update.message else None
        if not text or not text.startswith(self.prefix):
            return False
        first = text[len(self.prefix) :].split(maxsplit=1)[0]
        # отбрасываем возможный @botname
        command = first.split("@", 1)[0]
        return command in self.commands


class CallbackPayload:
    """Совпадает, если payload нажатой кнопки равен одному из заданных значений."""

    def __init__(self, *payloads: str) -> None:
        self.payloads = set(payloads)

    async def check(self, update: Update) -> bool:
        if update.callback is None:
            return False
        return update.callback.payload in self.payloads


class HasMedia:
    """Совпадает, если сообщение содержит вложения указанных типов.

    Без аргументов — любое вложение. С аргументами — хотя бы одно совпадение.

    Примеры типов: "image", "video", "audio", "file".
    """

    def __init__(self, *types: str) -> None:
        self.types = set(types)

    async def check(self, update: Update) -> bool:
        if update.message is None or update.message.body is None:
            return False
        atts = update.message.body.attachments
        if not atts:
            return False
        if not self.types:
            return True
        return any(a.type in self.types for a in atts)
