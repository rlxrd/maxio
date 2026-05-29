# DI — внедрение зависимостей

maxio резолвит аргументы хэндлера по аннотации типа. Объявляйте только то, что нужно — фреймворк подставит сам.

```python
@app.message()
async def handler(message: Message, bot: Bot, fsm: FSMContext) -> None:
    me = await bot.get_me()
    await message.answer(f"Привет от @{me.username}")
```

## Доступные типы

| Тип | Когда доступен |
|---|---|
| `Update` | всегда |
| `Bot` | всегда |
| `FSMContext` | всегда (когда есть `user_id`) |
| `Message` | `message_created`, `message_edited`, `message_callback` |
| `Callback` | `message_callback` |
| `User` | отправитель / инициатор (в большинстве событий) |
| `Chat` | `message_chat_created` |

## Optional — безопасный резолв

Если тип недоступен для данного события — `MaxError`. Но если объявить `X | None` или `Optional[X]` — вернётся `None`:

```python
@app.bot_started()
async def on_start(update: Update, message: Message | None) -> None:
    # message == None — bot_started не несёт объект Message
    if message:
        await message.answer("...")
    else:
        await bot.send_message("Привет!", chat_id=update.chat_id)
```

```python
@app.user_added()
async def on_join(update: Update, bot: Bot, user: User | None) -> None:
    if user and update.chat_id:
        await bot.send_message(f"Привет, {user.full_name}!", chat_id=update.chat_id)
```

## Примеры

### Только нужное

```python
@app.message()
async def simple(message: Message) -> None:
    await message.answer("ok")  # bot не нужен — не объявляем

@app.message()
async def with_bot(message: Message, bot: Bot) -> None:
    me = await bot.get_me()
    await message.answer(f"Я: @{me.username}")
```

### User из разных событий

`User` резолвится из первого доступного источника: `message.sender`, `callback.user`, `update.user`.

```python
@app.message()
async def show_user(message: Message, user: User) -> None:
    await message.answer(f"Ты: {user.full_name} (id={user.user_id})")

@app.callback()
async def show_clicker(callback: Callback, user: User) -> None:
    await callback.answer(notification=f"Нажал: {user.full_name}")
```

### FSMContext

```python
@app.message()
async def with_fsm(message: Message, fsm: FSMContext) -> None:
    await fsm.set_state(MyState.waiting)
    await message.answer("Жду ответа...")
```

## Несовместимый тип без дефолта

Если запросить тип, которого нет в контексте события, и не пометить его как Optional — `MaxError`:

```python
@app.message_removed()
async def bad(message: Message) -> None:  # MaxError: message недоступен
    ...

@app.message_removed()
async def ok(message: Message | None) -> None:  # None — безопасно
    ...
```
