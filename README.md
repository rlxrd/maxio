<p align="center">
  <img src="https://img.shields.io/pypi/v/maxio?label=PyPI&color=blue" alt="PyPI version">
  <img src="https://img.shields.io/pypi/pyversions/maxio" alt="Python versions">
  <img src="https://img.shields.io/pypi/dm/maxio?label=downloads" alt="Monthly downloads">
  <img src="https://img.shields.io/github/license/rlxrd/maxio?color=green" alt="License: MIT">
  <img src="https://img.shields.io/badge/type%20checked-mypy%20strict-brightgreen" alt="mypy strict">
</p>

<h1 align="center">maxio</h1>

<p align="center">
  Асинхронный Python-фреймворк для <a href="https://dev.max.ru/docs-api">MAX Bot API</a><br>
  с внедрением зависимостей по аннотациям типов.
</p>

---

Объявляйте в сигнатуре хэндлера только то, что нужно — фреймворк подставит из контекста сам:

```python
@app.message(F.text == "привет")
async def greet(message: Message, bot: Bot) -> None:
    await message.answer("Привет!")
```

Никаких `context["bot"]`, никакого `middleware_data`. Просто типы.

## Установка

```bash
pip install maxio
```

Python 3.10+, зависимости: `httpx` + `pydantic v2`.

## Быстрый старт

Получите токен у [@MasterBot](https://max.ru/MasterBot):

```python
import os
from maxio import Bot, Callback, F, InlineKeyboard, MaxBot, Message, Update
from maxio.keyboards import Button

app = MaxBot(os.environ["MAX_TOKEN"])


# Синяя кнопка Start шлёт событие bot_started (без message), а не /start.
@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    kb = InlineKeyboard().row(Button.callback("Нажми меня", "ping"))
    await bot.send_message("Привет!", chat_id=update.chat_id, keyboard=kb)


@app.message(F.text == "/help")
async def help_cmd(message: Message) -> None:
    await message.answer("Это бот на фреймворке maxio!")


@app.callback(F.data == "ping")
async def on_ping(callback: Callback) -> None:
    await callback.answer(notification="Понг!")
    if callback.message:
        await callback.message.answer("Ты нажал кнопку!")


@app.message()
async def echo(message: Message) -> None:
    await message.reply(message.text or "")


if __name__ == "__main__":
    app.run()
```

```bash
MAX_TOKEN=<ваш_токен> python bot.py
```


## Декораторы событий

Имена совпадают с типами событий MAX Bot API. Все 11 типов покрыты.

### Сообщения

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.message()` | `message_created` | новое сообщение |
| `@app.message_edited()` | `message_edited` | сообщение отредактировано |
| `@app.message_removed()` | `message_removed` | сообщение удалено (`update.message_id`, `chat_id`) |
| `@app.callback()` | `message_callback` | нажата inline-кнопка |

### Чаты

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.chat_created()` | `message_chat_created` | создан групповой чат с ботом |
| `@app.chat_title_changed()` | `chat_title_changed` | изменён заголовок (`update.title`) |

### Участники

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.user_added()` | `user_added` | пользователь добавлен (`update.inviter_id`) |
| `@app.user_removed()` | `user_removed` | пользователь удалён (`update.admin_id`) |

### Бот

| Декоратор | Тип события | Когда |
|---|---|---|
| `@app.bot_started()` | `bot_started` | нажата кнопка «Начать» (`update.payload`) |
| `@app.bot_added()` | `bot_added` | бот добавлен в чат/канал (`update.is_channel`) |
| `@app.bot_removed()` | `bot_removed` | бот удалён из чата/канала |

### Низкоуровневый

| Декоратор | Когда |
|---|---|
| `@app.event(*types)` | подписка на произвольные типы (или все — без аргументов) |

Несколько хэндлеров — первый подходящий выигрывает (first-match-wins).

### Чем `bot_started` отличается от `/start`

**Синяя кнопка Start в MAX не отправляет текст `/start`** — она шлёт отдельное событие
`bot_started`, в котором нет объекта `Message`. Отвечать нужно через `Bot`:

```python
@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    await bot.send_message("Привет!", chat_id=update.chat_id)

@app.message(Command("start"))   # ручной ввод /start
async def start_cmd(message: Message) -> None:
    await message.answer("Привет!")
```


## F — Magic Filter

`F` — ленивый объект для построения фильтров. Читается как обычное выражение:

```python
from maxio import F

@app.message(F.text == "да")
@app.message(F.text.startswith("/"))
@app.message(F.text.in_("стоп", "отмена"))
@app.message(F.photo)                        # есть фото-вложение
@app.callback(F.data == "buy")
@app.callback(F.data.in_("buy", "sell"))
```

**Шорткаты** — наиболее частые поля доступны напрямую:

| Выражение | Что проверяет |
|---|---|
| `F.text` | `update.message.text` |
| `F.data` | `update.callback.payload` |
| `F.payload` | `update.payload` (deep link в `bot_started`) |
| `F.photo` / `F.image` | есть вложение типа `image` |
| `F.video` | есть вложение типа `video` |
| `F.audio` | есть вложение типа `audio` |
| `F.file` / `F.document` | есть вложение типа `file` |

**Полный путь** тоже работает: `F.message.sender.user_id == 5`

**Операторы**:

```python
F.text == "да"               # равенство
F.text != "нет"              # неравенство
F.text.startswith("/")       # начинается с
F.text.endswith("!")         # заканчивается на
F.text.contains("ключ")      # содержит подстроку
F.data.in_("a", "b", "c")   # входит в список
F.data.not_in_("x", "y")    # не входит в список
~F.photo                     # NOT
F.text & F.photo             # AND
F.text | F.data              # OR
```

Старые фильтры `Command`, `CallbackPayload`, `HasMedia` тоже работают — `F` не замена, а дополнение.


## Фильтры

Любой callable `(Update) -> bool` или объект с `async def check(update) -> bool` — фильтр.
Несколько фильтров в декораторе объединяются как AND.

```python
from maxio import Command, HasMedia

@app.message(Command("help"))
async def help_cmd(message: Message) -> None: ...

# Функция как фильтр
def is_private(update: Update) -> bool:
    return bool(update.message and update.message.recipient.chat_type == "dialog")

@app.message(is_private, F.text)
async def echo(message: Message) -> None: ...

# HasMedia — по типу вложения
@app.message(HasMedia("image"))
async def got_photo(message: Message) -> None: ...
```


## DI — внедрение зависимостей

Объявляйте в сигнатуре хэндлера только нужное — фреймворк резолвит по типу:

```python
@app.message()
async def handler(message: Message, bot: Bot, fsm: FSMContext) -> None: ...
```

**Доступные типы:**

| Тип | Когда доступен |
|---|---|
| `Update` | всегда |
| `Bot` | всегда |
| `FSMContext` | всегда |
| `Message` | `message_created`, `message_edited`, `message_callback` |
| `Callback` | `message_callback` |
| `User` | отправитель / инициатор события |
| `Chat` | `message_chat_created` |

**Optional** — безопасно, если тип недоступен для данного события:

```python
@app.bot_started()
async def on_start(update: Update, message: Message | None) -> None:
    # message будет None — bot_started не несёт объект Message
    ...
```

Несовместимый тип (не Optional и нет дефолта) → понятная ошибка `MaxError`.


## Middleware

Middleware — callable-объект или функция, прикрепляется к `MaxBot` или `Router`.

**Порядок:** `app.outer → router.outer → app.inner → router.inner → handler`

### Outer middleware

Оборачивает всю диспетчеризацию. Может прервать цепочку (не вызвать `call_next`).
Аргументы резолвятся по DI — объявляйте только нужное:

```python
from maxio.middleware import CallNextOuter

async def timing(update: Update, call_next: CallNextOuter) -> bool:
    t = time.monotonic()
    result = await call_next()
    print(f"{update.update_type} → {time.monotonic() - t:.3f}s")
    return result

app.outer_middleware(timing)                             # все апдейты
app.outer_middleware(timing, UpdateType.MESSAGE_CREATED) # только нужный тип
```

DI в outer middleware: можно инжектировать `Bot`, `User`, `Message | None` и т.д.:

```python
async def require_auth(call_next: CallNextOuter, user: User | None) -> bool:
    if not user or user.user_id not in ALLOWED:
        return False
    return await call_next()
```

### Inner middleware

Вызывается после выбора хэндлера. Получает `CallNextInner` и любые DI-типы.
`HandlerKwargs` — уже резолвленные аргументы, которые пойдут в хэндлер:

```python
from maxio.middleware import CallNextInner, HandlerKwargs

async def log_args(call_next: CallNextInner, kwargs: HandlerKwargs) -> None:
    print("хэндлер получит:", list(kwargs.keys()))
    await call_next()

app.inner_middleware(log_args)
```


## Роутеры

```python
from maxio import Router

admin = Router()
users = Router()
app.include_routers(admin, users)

@admin.message(Command("ban"))
async def ban(message: Message) -> None: ...
```

Middleware на роутере срабатывает только если хэндлер принадлежит этому роутеру.


## FSM — диалоги с состоянием

```python
from maxio import StatesGroup, State, StateFilter, FSMContext

class Form(StatesGroup):
    waiting_name = State()
    waiting_age  = State()

@app.message(Command("register"))
async def start_form(message: Message, fsm: FSMContext) -> None:
    await fsm.set_state(Form.waiting_name)
    await message.answer("Как тебя зовут?")

@app.message(StateFilter(Form.waiting_name))
async def got_name(message: Message, fsm: FSMContext) -> None:
    await fsm.update_data(name=message.text)
    await fsm.set_state(Form.waiting_age)
    await message.answer("Сколько тебе лет?")

@app.message(StateFilter(Form.waiting_age))
async def got_age(message: Message, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    await fsm.clear()
    await message.answer(f"{data['name']}, {message.text} лет — записал!")

@app.message(Command("cancel"), StateFilter(Form.waiting_name, Form.waiting_age))
async def cancel(message: Message, fsm: FSMContext) -> None:
    await fsm.clear()
    await message.answer("Отменено.")
```

`FSMContext` инжектируется по типу. По умолчанию — `MemoryStorage`.
Своё хранилище: `MaxBot(token, storage=MyStorage())`.


## Медиа

```python
from maxio import HasMedia, F, media
from maxio.enums import UploadType
from pathlib import Path

# Отправить картинку из файла
@app.message(Command("photo"))
async def send_photo(message: Message, bot: Bot) -> None:
    token = await bot.upload(Path("photo.jpg"), UploadType.IMAGE)
    await message.answer("Держи!", attachments=[media.image(token)])

# Принять фото через F-фильтр
@app.message(F.photo)
async def got_photo(message: Message) -> None:
    for photo in message.photos:   # list[PhotoAttachmentPayload]
        await message.answer(f"URL: {photo.url}")

# Принять файл
@app.message(F.file)
async def got_file(message: Message) -> None:
    for f in message.files:        # list[FileAttachmentPayload]
        await message.answer(f"{f.filename} — {f.size} байт")
```

`Bot.upload` принимает `bytes`, `IO[bytes]` или `Path`.
Типы: `IMAGE`, `VIDEO`, `AUDIO`, `FILE`.


## Inline-клавиатуры

```python
from maxio import InlineKeyboard
from maxio.keyboards import Button
from maxio.enums import Intent

kb = (
    InlineKeyboard()
    .row(
        Button.callback("✅ Ок", "ok", intent=Intent.POSITIVE),
        Button.callback("❌ Отмена", "cancel", intent=Intent.NEGATIVE),
    )
    .row(Button.link("Сайт", "https://example.com"))
    .row(Button.request_contact("📱 Поделиться номером"))
)
await message.answer("Выбери:", keyboard=kb)
```


## MaxBot — параметры запуска

```python
app = MaxBot(
    token="...",
    storage=MyStorage(),      # FSM-хранилище (по умолч. MemoryStorage)
    timeout=60.0,             # таймаут HTTP-запросов в секундах (по умолч. 100.0)
    mask_token_in_logs=True,  # скрыть токен в логах httpx (по умолч. True)
)

app.run()                     # запуск polling, блокирующий
# или
await app.start_polling()     # async-вариант
```


## Методы Bot

```python
await bot.get_me()
await bot.send_message(text, chat_id=..., user_id=..., keyboard=..., attachments=...)
await bot.edit_message(message_id, text=..., keyboard=..., attachments=...)
await bot.delete_message(message_id)
await bot.get_message(message_id)
await bot.get_messages(chat_id)
await bot.answer_callback(callback_id, notification=..., payload=...)
await bot.get_chats()
await bot.upload(file, UploadType.IMAGE)
```


## Возможности

- Long polling с автоматическим переподключением
- **Все 11 типов событий** MAX Bot API — именованные декораторы для каждого
- **F (MagicFilter)** — ленивые фильтры-выражения: `F.text == "да"`, `F.photo`, `F.data.in_(...)`
- Роутеры (`Router`) и `include_routers` для разбивки хэндлеров
- **DI в middleware** — `CallNextOuter`, `CallNextInner`, `HandlerKwargs` инжектируются по типу
- **Optional в DI** — `Message | None` подставляет `None` вместо ошибки
- Middleware: outer / inner, на `MaxBot` и на `Router`, по типам апдейтов
- FSM: `StatesGroup`, `State`, `FSMContext`, `StateFilter`, `MemoryStorage`
- Медиа: `Bot.upload()`, `media.image/video/audio/file()`, фильтры `F.photo` / `HasMedia`
- Inline-клавиатуры: callback / link / request_contact / request_geo_location
- Сахар: `message.answer()`, `message.reply()`, `callback.answer()`, `callback.message.answer()`
- Pydantic v2, `py.typed`, `mypy --strict` ✅

---

## Спонсоры

<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://sudoteach.com">
        <b>sudoteach.com</b>
      </a>
      <br><br>
      Генеральный спонсор.<br>
      Онлайн-школа программирования — там есть курс <b>«Боты на maxio»</b>: от установки до продакшна.
    </td>
    <td align="center" width="50%">
      <a href="https://bothost.ru">
        <b>bothost.ru</b>
      </a>
      <br><br>
      Официальный партнёр.<br>
      Хостинг для ботов MAX и Telegram — деплой в один клик, мониторинг, автозапуск.
    </td>
  </tr>
</table>

## Лицензия

[MIT](LICENSE)
