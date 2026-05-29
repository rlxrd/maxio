# Справочник API

## MaxBot

```python
from maxio import MaxBot

app = MaxBot(
    token="...",
    storage=MemoryStorage(),   # FSM-хранилище (по умолч. MemoryStorage)
    timeout=60.0,              # таймаут HTTP-запросов в секундах (по умолч. 100.0)
    mask_token_in_logs=True,   # скрыть токен в логах httpx (по умолч. True)
)
```

### Запуск

```python
app.run()                  # блокирующий polling
await app.start_polling()  # async-вариант
```

### Регистрация

```python
app.include_routers(r1, r2, ...)

app.outer_middleware(fn)
app.outer_middleware(fn, UpdateType.MESSAGE_CREATED)
app.inner_middleware(fn)
```

---

## Bot — методы API

```python
from maxio import Bot
```

### get_me

```python
info = await bot.get_me()
# info.user_id, info.username, info.full_name
```

### send_message

```python
await bot.send_message(
    text,
    chat_id=...,         # или user_id=...
    user_id=...,
    keyboard=kb,         # InlineKeyboard
    attachments=[...],   # media.image/video/audio/file
    notify=True,         # уведомление пользователю
    format=TextFormat.MARKDOWN,
)
```

### edit_message

```python
await bot.edit_message(
    message_id,
    text="новый текст",
    keyboard=kb,
    attachments=[...],
)
```

### delete_message

```python
await bot.delete_message(message_id)
```

### get_message / get_messages

```python
msg = await bot.get_message(message_id)
msgs = await bot.get_messages(chat_id)
```

### answer_callback

```python
await bot.answer_callback(callback_id, notification="Готово!", payload="...")
```

### get_chats

```python
chats = await bot.get_chats()
```

### upload

```python
token = await bot.upload(file, UploadType.IMAGE)
# file: Path | bytes | IO[bytes]
# UploadType: IMAGE, VIDEO, AUDIO, FILE
```

---

## Message — сахар

```python
await message.answer(text, keyboard=kb, attachments=[...])
await message.reply(text, keyboard=kb, attachments=[...])
```

`answer` — ответить в тот же чат. `reply` — ответить с цитатой.

---

## Callback — сахар

```python
await callback.answer(notification="Текст уведомления", payload="...")
await callback.answer()  # без уведомления
```

`callback.message` — сообщение, к которому привязана кнопка (если доступно).

---

## Перечисления

```python
from maxio.enums import (
    UpdateType,    # MESSAGE_CREATED, MESSAGE_EDITED, …
    UploadType,    # IMAGE, VIDEO, AUDIO, FILE
    TextFormat,    # MARKDOWN, HTML
    Intent,        # POSITIVE, NEGATIVE, DEFAULT
    ChatType,      # DIALOG, CHAT, CHANNEL
    ButtonType,    # CALLBACK, LINK, REQUEST_CONTACT, REQUEST_GEO_LOCATION
)
```

---

## Исключения

```python
from maxio import MaxError, MaxApiError

# MaxError — внутренняя ошибка фреймворка (например, неизвестный DI-тип)
# MaxApiError — ошибка от MAX Bot API (содержит HTTP-статус и тело ответа)
```
