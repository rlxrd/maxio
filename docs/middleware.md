# Middleware

Middleware — callable-объект или функция, которая оборачивает обработку апдейта.

## Порядок выполнения

```
app.outer → router.outer → app.inner → router.inner → handler
```

- **Outer** — оборачивает всю диспетчеризацию, включая поиск хэндлера
- **Inner** — вызывается после выбора хэндлера, перед его запуском

## Outer middleware

Возвращает `bool` — `True` значит «обработано», `False` — отклонено.

Аргументы резолвятся по DI — объявляйте только то, что нужно:

```python
from maxio.middleware import CallNextOuter
from maxio import Update

async def timing(update: Update, call_next: CallNextOuter) -> bool:
    import time
    t = time.monotonic()
    result = await call_next()
    print(f"{update.update_type} → {time.monotonic() - t:.3f}s")
    return result

app.outer_middleware(timing)
```

Прерывание цепочки — не вызвать `call_next`:

```python
ADMIN_IDS = {123456789}

async def require_admin(call_next: CallNextOuter, user: User | None) -> bool:
    if not user or user.user_id not in ADMIN_IDS:
        return False           # хэндлер не вызовется
    return await call_next()

admin_router.outer_middleware(require_admin)
```

Фильтрация по типу апдейта:

```python
from maxio.enums import UpdateType

async def log_messages(update: Update, call_next: CallNextOuter) -> bool:
    print(f"Сообщение от {update.user.user_id if update.user else '?'}")
    return await call_next()

app.outer_middleware(log_messages, UpdateType.MESSAGE_CREATED)
```

### Класс как middleware

```python
class TimingMiddleware:
    async def __call__(self, update: Update, call_next: CallNextOuter) -> bool:
        t = time.monotonic()
        result = await call_next()
        print(f"{update.update_type} → {time.monotonic() - t:.3f}s")
        return result

app.outer_middleware(TimingMiddleware())
```

## Inner middleware

Вызывается после того, как хэндлер найден. Не возвращает значение.

`HandlerKwargs` — словарь уже резолвленных аргументов, которые пойдут в хэндлер:

```python
from maxio.middleware import CallNextInner, HandlerKwargs

async def log_args(call_next: CallNextInner, kwargs: HandlerKwargs) -> None:
    print("хэндлер получит:", list(kwargs.keys()))
    await call_next()

app.inner_middleware(log_args)
```

Можно инжектировать любые DI-типы:

```python
async def check_ban(call_next: CallNextInner, user: User | None) -> None:
    if user and is_banned(user.user_id):
        return  # хэндлер не вызовется
    await call_next()

app.inner_middleware(check_ban)
```

## Middleware на роутере

Middleware роутера срабатывает только если хэндлер принадлежит этому роутеру:

```python
admin = Router()
admin.outer_middleware(require_admin)

@admin.message(Command("ban"))
async def ban(message: Message) -> None: ...
```

`require_admin` сработает только для хэндлеров `admin`, а не для всего приложения.

## Итог: что доступно в DI

| Тип | Outer | Inner |
|---|---|---|
| `Update` | ✅ | ✅ |
| `Bot` | ✅ | ✅ |
| `Message`, `User`, `Callback`… | ✅ | ✅ |
| `CallNextOuter` | ✅ | — |
| `CallNextInner` | — | ✅ |
| `HandlerKwargs` | — | ✅ |
