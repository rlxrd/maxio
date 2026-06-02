# Хэндлеры

Хэндлер — асинхронная функция, привязанная к типу события через декоратор. Первый подходящий хэндлер выигрывает (first-match-wins).

!!! note "Предполагаемый setup"
    Во всех примерах этой страницы подразумевается:
    ```python
    import os
    from maxio import MaxBot
    app = MaxBot(os.environ["MAX_TOKEN"])
    ```

## Все типы событий

### Сообщения

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.message()` | `message_created` | новое входящее сообщение |
| `@app.message_edited()` | `message_edited` | сообщение отредактировано |
| `@app.message_removed()` | `message_removed` | сообщение удалено |
| `@app.callback()` | `message_callback` | нажата inline-кнопка |

### Чаты

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.chat_created()` | `message_chat_created` | создан групповой чат с ботом |
| `@app.chat_title_changed()` | `chat_title_changed` | изменён заголовок чата |

### Участники

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.user_added()` | `user_added` | пользователь добавлен в чат |
| `@app.user_removed()` | `user_removed` | пользователь удалён / вышел |

### Бот

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.bot_started()` | `bot_started` | нажата кнопка «Начать» |
| `@app.bot_added()` | `bot_added` | бот добавлен в чат или канал |
| `@app.bot_removed()` | `bot_removed` | бот удалён из чата или канала |

### Низкоуровневый

```python
from maxio.enums import UpdateType

@app.event(UpdateType.MESSAGE_CREATED, UpdateType.MESSAGE_EDITED)
async def on_any_message(update: Update) -> None: ...

@app.event()  # все типы
async def on_everything(update: Update) -> None: ...
```

---

## Примеры по типам

### message — входящее сообщение

```python
from maxio import Command, F, Message

@app.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Привет! Это справка.")

@app.message(F.text == "да")
async def on_yes(message: Message) -> None:
    await message.answer("Ты сказал «да»!")

@app.message()  # fallback — без фильтров
async def echo(message: Message) -> None:
    await message.reply(message.text or "")
```

Доступные поля через DI: `Message`, `User`, `Bot`, `Update`, `FSMContext`.

### message_edited — редактирование

```python
@app.message_edited()
async def on_edit(message: Message) -> None:
    await message.answer(f"Ты отредактировал: «{message.text}»")
```

### message_removed — удаление

!!! warning "Нет объекта Message"
    Событие несёт только `update.message_id` и `update.chat_id` — объект `Message` не приходит.

```python
@app.message_removed()
async def on_removed(update: Update) -> None:
    print(f"Удалено {update.message_id} в чате {update.chat_id}")
```

### callback — нажатие кнопки

```python
from maxio import Callback, F

@app.callback(F.data == "help")
async def cb_help(callback: Callback) -> None:
    await callback.answer(notification="Открываю справку…")
    if callback.message:
        await callback.message.answer("Вот справка!")

@app.callback()  # fallback
async def cb_fallback(callback: Callback) -> None:
    await callback.answer(notification=f"Кнопка: {callback.payload}")
```

### bot_started — кнопка «Начать»

!!! warning "Нет объекта Message"
    `bot_started` — это отдельное событие, не сообщение. Отвечать через `bot.send_message`.

```python
@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    # update.payload — deep link (если был передан при запуске)
    await bot.send_message("Привет!", chat_id=update.chat_id)
```

### bot_added / bot_removed

```python
@app.bot_added()
async def on_bot_added(update: Update, bot: Bot) -> None:
    kind = "канал" if update.is_channel else "чат"
    if update.chat_id and not update.is_channel:
        await bot.send_message("Привет, я готов!", chat_id=update.chat_id)

@app.bot_removed()
async def on_bot_removed(update: Update) -> None:
    print(f"Удалён из чата {update.chat_id}")
```

### user_added / user_removed

```python
from maxio import User

@app.user_added()
async def on_user_added(update: Update, bot: Bot, user: User | None) -> None:
    if user and update.chat_id:
        await bot.send_message(
            f"Добро пожаловать, {user.full_name}!",
            chat_id=update.chat_id,
        )

@app.user_removed()
async def on_user_removed(update: Update, user: User | None) -> None:
    name = user.full_name if user else "Кто-то"
    print(f"{name} покинул чат {update.chat_id}")
```

### chat_created / chat_title_changed

```python
@app.chat_created()
async def on_chat_created(update: Update, bot: Bot) -> None:
    if update.chat_id:
        await bot.send_message("Чат создан!", chat_id=update.chat_id)

@app.chat_title_changed()
async def on_title(update: Update) -> None:
    # update.title — новое название, update.user — кто менял
    print(f"Чат {update.chat_id} → «{update.title}»")
```

---

## Несколько фильтров — AND

```python
@app.message(Command("buy"), is_private)
async def buy(message: Message) -> None: ...
```

Все фильтры объединяются как AND. Порядок хэндлеров — порядок регистрации.
