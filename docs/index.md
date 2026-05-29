# maxio

**Асинхронный Python-фреймворк для [MAX Bot API](https://dev.max.ru/docs-api)** с внедрением зависимостей по аннотациям типов.

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

Python 3.10+. Зависимости: `httpx`, `pydantic v2`.

## Получить токен

Напишите [@MasterBot](https://max.ru/MasterBot) в MAX — он выдаст токен за несколько шагов.

## Первый бот

```python
import os
from maxio import Bot, Callback, F, InlineKeyboard, MaxBot, Message, Update
from maxio.keyboards import Button

app = MaxBot(os.environ["MAX_TOKEN"])


@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    kb = InlineKeyboard().row(Button.callback("Нажми меня", "ping"))
    await bot.send_message("Привет!", chat_id=update.chat_id, keyboard=kb)


@app.message(F.text == "/help")
async def help_cmd(message: Message) -> None:
    await message.answer("Это бот на maxio!")


@app.callback(F.data == "ping")
async def on_ping(callback: Callback) -> None:
    await callback.answer(notification="Понг!")


@app.message()
async def echo(message: Message) -> None:
    await message.reply(message.text or "")


if __name__ == "__main__":
    app.run()
```

```bash
MAX_TOKEN=<ваш_токен> python bot.py
```

## Что умеет

- Long polling с автоматическим переподключением
- **Все 11 типов событий** MAX Bot API — именованный декоратор для каждого
- **F (MagicFilter)** — `F.text == "да"`, `F.photo`, `F.data.in_(...)`
- **DI по аннотациям** — `message: Message`, `bot: Bot`, `fsm: FSMContext` без лишнего кода
- **Optional в DI** — `Message | None` вместо ошибки, если тип недоступен
- **Middleware** (outer / inner) с полным DI на `MaxBot` и `Router`
- **Роутеры** — разбивка хэндлеров по модулям
- **FSM** — диалоги с состоянием, `MemoryStorage` из коробки
- **Медиа** — загрузка и приём фото / видео / аудио / файлов
- **Клавиатуры** — callback / link / request_contact / request_geo_location
- Pydantic v2, `py.typed`, `mypy --strict` ✅
