# Быстрый старт

## Установка

```bash
pip install maxio
```

Python 3.10+. Зависимости устанавливаются автоматически: `httpx`, `pydantic`.

## Получить токен

1. Открой MAX и найди [@MasterBot](https://max.ru/MasterBot)
2. Нажми «Начать» и следуй инструкциям
3. Скопируй токен

!!! warning "Не коммить токен"
    Храни токен в переменной окружения, а не в коде:
    ```bash
    export MAX_TOKEN="твой_токен_здесь"
    ```

## Минимальный бот

```python
import os
from maxio import MaxBot, Message

app = MaxBot(os.environ["MAX_TOKEN"])


@app.message()
async def echo(message: Message) -> None:
    await message.reply(message.text or "")


if __name__ == "__main__":
    app.run()
```

```bash
python bot.py
```

## Кнопка «Начать»

!!! warning "bot_started ≠ /start"
    В MAX синяя кнопка Start шлёт событие `bot_started`, а **не** текст `/start`.
    Используй `@app.bot_started()` — это отдельный декоратор.

```python
import os
from maxio import Bot, MaxBot, Update

app = MaxBot(os.environ["MAX_TOKEN"])


@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    # update.chat_id — чат, update.payload — deep link (если был)
    await bot.send_message("Привет! Напиши /help", chat_id=update.chat_id)


if __name__ == "__main__":
    app.run()
```

## Команды

```python
import os
from maxio import Command, MaxBot, Message

app = MaxBot(os.environ["MAX_TOKEN"])


@app.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Команды: /help /about")


@app.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer("Бот на фреймворке maxio")


if __name__ == "__main__":
    app.run()
```

## Кнопки

```python
import os
from maxio import Callback, Command, F, InlineKeyboard, MaxBot, Message
from maxio.keyboards import Button

app = MaxBot(os.environ["MAX_TOKEN"])


@app.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    kb = (
        InlineKeyboard()
        .row(Button.callback("Да", "yes"), Button.callback("Нет", "no"))
    )
    await message.answer("Выбери:", keyboard=kb)


@app.callback(F.data == "yes")
async def on_yes(callback: Callback) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer("Ты нажал «Да»!")


@app.callback(F.data == "no")
async def on_no(callback: Callback) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer("Ты нажал «Нет»!")


if __name__ == "__main__":
    app.run()
```

!!! note "callback.answer vs callback.message.answer"
    `callback.answer(notification=...)` — всплывающее уведомление (MAX может не показывать).
    `callback.message.answer(...)` — обычное сообщение в чат, всегда отображается.

## Форматирование текста

MAX поддерживает Markdown и HTML через параметр `format`:

=== "Markdown"

    ```python
    import os
    from maxio import MaxBot, Message
    from maxio.enums import TextFormat

    app = MaxBot(os.environ["MAX_TOKEN"])


    @app.message()
    async def handler(message: Message) -> None:
        await message.answer(
            "**Жирный** _курсив_ `код`\n[Ссылка](https://max.ru)",
            format=TextFormat.MARKDOWN,
        )
    ```

=== "HTML"

    ```python
    import os
    from maxio import MaxBot, Message
    from maxio.enums import TextFormat

    app = MaxBot(os.environ["MAX_TOKEN"])


    @app.message()
    async def handler(message: Message) -> None:
        await message.answer(
            "<b>Жирный</b> <i>курсив</i> <code>код</code>",
            format=TextFormat.HTML,
        )
    ```

`format` работает в `message.answer()`, `message.reply()`, `bot.send_message()` и `bot.edit_message()`.

## Следующие шаги

- [Хэндлеры](handlers.md) — все 11 типов событий
- [Фильтры и F](filters.md) — фильтровать по тексту, медиа, payload
- [DI — зависимости](di.md) — что инжектируется и когда
- [FSM](fsm.md) — многошаговые диалоги
- [Управление чатами](chats.md) — участники, админы, вебхуки
