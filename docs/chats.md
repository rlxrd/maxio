# Управление чатами

maxio покрывает все эндпоинты для работы с чатами MAX Bot API.

## Информация о чате

```python
import os
from maxio import Bot, Command, MaxBot, Message
from maxio.enums import ChatAction

app = MaxBot(os.environ["MAX_TOKEN"])


@app.message(Command("chatinfo"))
async def cmd_chatinfo(message: Message, bot: Bot) -> None:
    chat = await bot.get_chat(message.chat_id)
    await message.answer(
        f"Чат: {chat.title}\n"
        f"Тип: {chat.type}\n"
        f"Участников: {chat.participants_count}"
    )
```

Список всех чатов бота:

```python
@app.message(Command("chats"))
async def cmd_chats(message: Message, bot: Bot) -> None:
    result = await bot.get_chats(count=50)
    lines = [f"• {c.title} ({c.chat_id})" for c in result.chats]
    await message.answer("\n".join(lines) or "Чатов нет")
```

Пагинация через `result.marker`:

```python
result = await bot.get_chats(count=50)
all_chats = list(result.chats)

while result.marker:
    result = await bot.get_chats(count=50, marker=result.marker)
    all_chats.extend(result.chats)
```

## Изменить название чата

```python
@app.message(Command("rename"))
async def cmd_rename(message: Message, bot: Bot) -> None:
    new_title = (message.text or "").removeprefix("/rename").strip()
    if not new_title:
        await message.answer("Используй: /rename Новое название")
        return
    await bot.update_chat(message.chat_id, title=new_title)
    await message.answer(f"Чат переименован в «{new_title}»")
```

## Typing indicator

```python
import asyncio
from maxio import Bot, Command, Message
from maxio.enums import ChatAction


@app.message(Command("generate"))
async def cmd_generate(message: Message, bot: Bot) -> None:
    await bot.send_chat_action(message.chat_id, ChatAction.TYPING_ON)
    await asyncio.sleep(2)   # долгая операция
    await message.answer("Готово!")
```

Доступные действия: `TYPING_ON`, `TYPING_OFF`, `SENDING_PHOTO`, `SENDING_VIDEO`, `SENDING_AUDIO`, `SENDING_FILE`, `MARK_SEEN`.

## Закреплённые сообщения

```python
from maxio import Bot, Command, Message


@app.message(Command("pinned"))
async def cmd_pinned(message: Message, bot: Bot) -> None:
    msg = await bot.get_pinned_message(message.chat_id)
    if msg:
        await message.answer(f"Закреплено: {msg.text}")
    else:
        await message.answer("Нет закреплённого сообщения")


@app.message(Command("pin"))
async def cmd_pin(message: Message, bot: Bot) -> None:
    if message.link and message.link.message and message.link.message.mid:
        await bot.pin_message(message.chat_id, message.link.message.mid)
        await message.answer("Закреплено!")
    else:
        await message.answer("Ответь на сообщение, которое нужно закрепить")


@app.message(Command("unpin"))
async def cmd_unpin(message: Message, bot: Bot) -> None:
    await bot.unpin_message(message.chat_id)
    await message.answer("Откреплено")
```

## Участники

### Список

```python
from maxio import Bot, Command, Message


@app.message(Command("members"))
async def cmd_members(message: Message, bot: Bot) -> None:
    result = await bot.get_chat_members(message.chat_id, count=100)
    lines = [f"• {m.first_name} — {m.role}" for m in result.members]
    await message.answer("\n".join(lines))
```

Пагинация через `result.marker`:

```python
result = await bot.get_chat_members(chat_id, count=50)
all_members = list(result.members)

while result.marker:
    result = await bot.get_chat_members(chat_id, count=50, marker=result.marker)
    all_members.extend(result.members)
```

### Добавить и удалить

```python
from maxio import Bot, Command, Message


@app.message(Command("kick"))
async def cmd_kick(message: Message, bot: Bot) -> None:
    if not message.link or not message.link.sender:
        await message.answer("Ответь на сообщение пользователя")
        return
    user_id = message.link.sender.user_id
    await bot.remove_chat_member(message.chat_id, user_id)
    await message.answer("Пользователь удалён")
```

## Администраторы

```python
from maxio import Bot, Command, Message


@app.message(Command("admins"))
async def cmd_admins(message: Message, bot: Bot) -> None:
    admins = await bot.get_chat_admins(message.chat_id)
    lines = [f"• {a.first_name} ({a.user_id})" for a in admins]
    await message.answer("Администраторы:\n" + "\n".join(lines))
```

## Вебхуки

Альтернатива long polling — получать события через HTTP POST на ваш сервер.

```python
import os
from maxio import Bot, Command, MaxBot, Message, Update

app = MaxBot(os.environ["MAX_TOKEN"])


@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    await bot.subscribe(
        url="https://yourserver.com/webhook",
        update_types=["message_created", "message_callback"],
    )
```

Посмотреть активные подписки:

```python
@app.message(Command("webhooks"))
async def cmd_webhooks(message: Message, bot: Bot) -> None:
    subs = await bot.get_subscriptions()
    if not subs.subscriptions:
        await message.answer("Подписок нет")
        return
    lines = [f"• {s.url}" for s in subs.subscriptions]
    await message.answer("\n".join(lines))
```

!!! note "HTTPS обязателен"
    URL для вебхука должен быть доступен из интернета и работать по HTTPS.
