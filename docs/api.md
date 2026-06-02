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
app.stop()                 # остановить polling
```

### Подключение роутеров и middleware

```python
app.include_routers(r1, r2, ...)

app.outer_middleware(fn)
app.outer_middleware(fn, UpdateType.MESSAGE_CREATED)
app.inner_middleware(fn)
```

---

## Bot

`Bot` — исполнитель HTTP-запросов. Каждый метод создаёт соответствующий [`MaxMethod`](methods.md) и вызывает `Bot.__call__`.

```python
from maxio import Bot
```

### Информация о боте

```python
info = await bot.get_me()
# → BotInfo: user_id, username, full_name, description, avatar_url
```

### Сообщения

```python
await bot.send_message(
    text,
    chat_id=...,           # или user_id=...
    user_id=...,
    keyboard=kb,           # InlineKeyboard
    attachments=[...],     # media.image/video/audio/file
    notify=True,
    format=TextFormat.MARKDOWN,
    disable_link_preview=False,
)

await bot.edit_message(message_id, text="новый текст", keyboard=kb)

await bot.delete_message(message_id)

msg  = await bot.get_message(message_id)
msgs = await bot.get_messages(chat_id=..., count=50, from_time=..., to_time=...)
```

### Callbacks

```python
await bot.answer_callback(
    callback_id,
    notification="Готово!",   # всплывающее уведомление
    text="...",               # сообщение вместе с ответом
    keyboard=kb,
)
```

### Чаты

```python
chats = await bot.get_chats(count=50)
chat  = await bot.get_chat(chat_id)
chat  = await bot.update_chat(chat_id, title="Новое название", notify=True)
await bot.delete_chat(chat_id)
await bot.send_chat_action(chat_id, ChatAction.TYPING_ON)
```

### Закреплённые сообщения

```python
msg = await bot.get_pinned_message(chat_id)        # → Message | None
await bot.pin_message(chat_id, message_id, notify=True)
await bot.unpin_message(chat_id)
```

### Участники

```python
result = await bot.get_chat_members(chat_id, count=50, marker=None)
# result.members → list[ChatMember]
# result.marker  → int | None  (для пагинации)

await bot.add_chat_members(chat_id, user_ids=[1, 2, 3])
await bot.remove_chat_member(chat_id, user_id, block=False)

me = await bot.get_bot_chat_membership(chat_id)    # → ChatMember
await bot.leave_chat(chat_id)
```

### Администраторы

```python
admins = await bot.get_chat_admins(chat_id)        # → list[ChatMember]
await bot.add_chat_admin(chat_id, user_id)
await bot.remove_chat_admin(chat_id, user_id)
```

### Вебхуки

```python
subs = await bot.get_subscriptions()               # → SubscriptionList
sub  = await bot.subscribe(url, update_types=[...])
await bot.unsubscribe(url)
```

### Медиа

```python
token = await bot.upload(file, UploadType.IMAGE)
# file: Path | bytes | IO[bytes]

info = await bot.get_video_info(video_token)       # → VideoInfo
```

---

## Message

```python
await message.answer(text, keyboard=kb, attachments=[...], format=TextFormat.MARKDOWN)
await message.reply(text, keyboard=kb)   # с цитатой исходного сообщения
```

| Свойство | Тип | Описание |
|---|---|---|
| `text` | `str \| None` | Текст сообщения |
| `mid` | `str \| None` | ID сообщения |
| `chat_id` | `int \| None` | ID чата |
| `from_user` | `User \| None` | Отправитель |
| `attachments` | `list[Attachment]` | Все вложения |
| `photos` | `list[PhotoAttachmentPayload]` | Фотографии |
| `videos` | `list[VideoAttachmentPayload]` | Видео |
| `audio` | `list[AudioAttachmentPayload]` | Аудио |
| `files` | `list[FileAttachmentPayload]` | Файлы |

---

## Callback

```python
await callback.answer(notification="Текст уведомления")
await callback.answer()   # без уведомления
```

`callback.message` — сообщение, к которому привязана кнопка.  
`callback.payload` — строка payload из `Button.callback(...)`.

---

## Типы

### ChatMember

```python
from maxio.types.member import ChatMember, ChatMemberList

member.user_id
member.first_name
member.role          # ChatMemberRole: owner / admin / member
member.join_time
member.permissions   # list[str] | None
```

### Subscription

```python
from maxio.types.subscription import Subscription, SubscriptionList

sub.url
sub.update_types     # list[str] | None
sub.version          # str | None
```

### VideoInfo

```python
from maxio.types.video import VideoInfo

info.token
info.url
info.width
info.height
info.duration        # секунды
```

---

## Перечисления

```python
from maxio.enums import (
    UpdateType,       # MESSAGE_CREATED, MESSAGE_EDITED, MESSAGE_CALLBACK, …
    ChatAction,       # TYPING_ON, TYPING_OFF, SENDING_PHOTO, SENDING_VIDEO, …
    ChatMemberRole,   # OWNER, ADMIN, MEMBER
    UploadType,       # IMAGE, VIDEO, AUDIO, FILE
    TextFormat,       # MARKDOWN, HTML
    Intent,           # POSITIVE, NEGATIVE, DEFAULT
    ChatType,         # DIALOG, CHAT, CHANNEL
    ChatStatus,       # ACTIVE, REMOVED, LEFT, CLOSED, SUSPENDED
    ButtonType,       # CALLBACK, LINK, REQUEST_CONTACT, REQUEST_GEO_LOCATION, …
    MessageLinkType,  # FORWARD, REPLY
)
```

---

## Исключения

```python
from maxio import MaxError, MaxApiError
```

| Класс | Когда |
|---|---|
| `MaxError` | Внутренняя ошибка фреймворка (например, неизвестный DI-тип) |
| `MaxApiError` | HTTP-ошибка от MAX Bot API |

`MaxApiError` содержит:

- `status_code: int` — HTTP-статус
- `code: str | None` — код ошибки из API
- `message: str | None` — описание из API
