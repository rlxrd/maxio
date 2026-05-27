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

Объявляйте в сигнатуре хэндлера то, что нужно, — фреймворк подставит из контекста апдейта сам:

```python
@app.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer("Это бот на фреймворке maxio!")
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
from maxio import MaxBot, Message, Callback, Command, InlineKeyboard, Update, Bot
from maxio.keyboards import Button

app = MaxBot(token=os.environ["MAX_TOKEN"])


# Синяя кнопка Start шлёт событие bot_started (без message), а не /start.
@app.bot_started()
async def on_start(update: Update, bot: Bot):
    kb = InlineKeyboard().row(Button.callback("Нажми меня", "ping"))
    await bot.send_message("Привет! Я готов к работе.", chat_id=update.chat_id, keyboard=kb)


@app.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("Это бот на фреймворке maxio!")


@app.callback()
async def on_ping(callback: Callback):
    await callback.answer(notification="Понг!")        # всплывашка на кнопке
    if callback.message:
        await callback.message.answer("Ты нажал кнопку!")  # новое сообщение в чат


@app.message()
async def echo(message: Message):
    await message.reply(message.text or "")


if __name__ == "__main__":
    app.run()
```

```bash
MAX_TOKEN=<ваш_токен> python bot.py
```

## Внедрение зависимостей

| Тип             | Когда доступен                                  |
|-----------------|------------------------------------------------|
| `Message`       | `message_created`, `message_edited`, callback  |
| `Callback`      | `message_callback`                             |
| `User`          | отправитель/инициатор события                  |
| `Chat`          | `message_chat_created`                         |
| `Update`        | всегда (сырой апдейт)                           |
| `Bot`           | всегда (HTTP-клиент, прямой доступ к API)       |

Несовместимый тип → понятная ошибка `MaxError` с описанием проблемы.

## Декораторы событий

Имена декораторов совпадают с типами событий MAX Bot API.

| Декоратор               | Тип события         | Когда срабатывает                                            |
|-------------------------|---------------------|--------------------------------------------------------------|
| `@app.message()`        | `message_created`   | пришло **новое сообщение** от пользователя                   |
| `@app.message_edited()` | `message_edited`    | пользователь **отредактировал** своё сообщение               |
| `@app.callback()`       | `message_callback`  | нажата **inline-кнопка** (callback) под сообщением           |
| `@app.bot_started()`    | `bot_started`       | пользователь **запустил бота** — синяя кнопка **Start**      |
| `@app.event(*types)`    | любые               | подписка на произвольные типы апдейтов (или все — без аргументов) |

Несколько хэндлеров — первый подходящий выигрывает (first-match-wins).

### Чем `message` отличается от `bot_started`

Это частая путаница. **Синяя кнопка Start в MAX не отправляет текст `/start`** — она шлёт
отдельное событие `bot_started`, в котором **нет объекта `Message`** (есть `chat_id`, `user`
и опциональный `payload` из диплинка). Поэтому:

- хэндлер `@app.message(Command("start"))` ловит только **ручной ввод** `/start`;
- нажатие кнопки **Start** ловится через `@app.bot_started()`.

Если нужно, чтобы и кнопка, и команда здоровались одинаково — заведите оба обработчика.
Внутри `bot_started` нет `Message`, поэтому отвечать надо через `Bot`, указывая `chat_id`:

```python
@app.bot_started()
async def on_start(update: Update, bot: Bot):
    await bot.send_message("Привет! Нажми кнопку ниже.", chat_id=update.chat_id)


@app.message(Command("start"))           # ручной ввод /start
async def start_cmd(message: Message):
    await message.answer("Привет! Нажми кнопку ниже.")
```

### `callback` — нажатия inline-кнопок

Срабатывает, когда пользователь жмёт кнопку, созданную через `Button.callback(text, payload)`.
В обработчике доступен `Callback`; отвечать на нажатие нужно `callback.answer(...)`, иначе у
пользователя останется «крутилка» на кнопке. Исходное сообщение с кнопкой лежит в
`callback.message` — у него есть привычные `answer()` / `reply()` для отправки в тот же чат.

```python
@app.callback(CallbackPayload("buy"))    # фильтр по payload кнопки
async def buy(callback: Callback):
    await callback.answer(notification="Покупка оформлена")   # всплывашка на кнопке
    if callback.message:
        await callback.message.answer("Спасибо за заказ!")    # новое сообщение в чат
```

## Фильтры

```python
from maxio import Command, CallbackPayload

@app.message(Command("help"))
async def help_cmd(message: Message): ...

@app.callback(CallbackPayload("buy"))
async def buy(callback: Callback): ...

# Произвольный callable — тоже фильтр
@app.message(lambda u: u.message and len(u.message.text or "") > 100)
async def long_message(message: Message): ...
```

## Inline-клавиатуры

```python
from maxio import InlineKeyboard
from maxio.keyboards import Button

kb = (
    InlineKeyboard()
    .row(Button.callback("Да", "yes"), Button.callback("Нет", "no"))
    .row(Button.link("Сайт", "https://example.com"))
)
await message.answer("Выберите:", keyboard=kb)
```

## Методы API

```python
@app.message()
async def handler(message: Message, bot: Bot):
    me = await bot.get_me()
    await bot.send_message(chat_id=message.recipient.chat_id, text=f"Я — {me.name}")
    await bot.edit_message(message_id=message.message_id, text="Обновлено")
    await bot.delete_message(message_id=message.message_id)
    chats = await bot.get_chats()
```

## Возможности

- Long polling с автоматическим переподключением
- HTTP-клиент: `get_me`, `send_message`, `edit_message`, `delete_message`, `get_messages`, `get_chats`, `answer_callback`, `get_updates`
- Декораторы: `message`, `message_edited`, `callback`, `bot_started`, `event`
- DI по аннотациям типов — работает из коробки, без `Depends()`
- Фильтры: `Command`, `CallbackPayload`, любой `Callable`
- Inline-клавиатуры: callback / link / request_geo_location
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
