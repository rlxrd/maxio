from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from maxio.exceptions import MaxError

_MISSING = object()
_signature_cache: dict[Callable[..., Any], list[tuple[str, Any, Any]]] = {}


def get_handler_params(fn: Callable[..., Any]) -> list[tuple[str, Any, Any]]:
    """Возвращает [(имя_параметра, аннотация_типа, значение_по_умолчанию)], с кэшированием."""
    cached = _signature_cache.get(fn)
    if cached is not None:
        return cached

    hints = get_type_hints(fn)
    signature = inspect.signature(fn)
    params: list[tuple[str, Any, Any]] = []
    for name, parameter in signature.parameters.items():
        annotation = hints.get(name)
        default = (
            _MISSING if parameter.default is inspect.Parameter.empty else parameter.default
        )
        params.append((name, annotation, default))
    _signature_cache[fn] = params
    return params


def _lookup(annotation: Any, context: dict[type, Any]) -> Any:
    if annotation is None:
        return _MISSING
    if annotation in context:
        return context[annotation]
    if isinstance(annotation, type):
        for ctx_type, value in context.items():
            if issubclass(ctx_type, annotation):
                return value
    return _MISSING


def resolve_kwargs(
    fn: Callable[..., Any],
    context: dict[type, Any],
) -> dict[str, Any]:
    """Сопоставляет аргументы хэндлера с объектами контекста по аннотациям типов."""
    kwargs: dict[str, Any] = {}
    for name, annotation, default in get_handler_params(fn):
        value = _lookup(annotation, context)
        if value is _MISSING:
            if default is not _MISSING:
                continue
            type_name = getattr(annotation, "__name__", annotation)
            raise MaxError(
                f"Не удалось внедрить аргумент '{name}: {type_name}' в хэндлер "
                f"{fn.__name__!r}: такой тип недоступен для этого апдейта. "
                f"Доступны: {[t.__name__ for t in context]}."
            )
        kwargs[name] = value
    return kwargs
