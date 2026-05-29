# Быстрый старт

## Установка

```bash
pip install maxio
```

## Получить токен

1. Откройте MAX и найдите [@MasterBot](https://max.ru/MasterBot)
2. Нажмите «Начать» и следуйте инструкциям
3. Скопируйте токен

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
MAX_TOKEN=<токен> python bot.py
```

## Кнопка «Начать»

В MAX синяя кнопка **Start** не отправляет текст `/start` — она шлёт отдельное событие `bot_started`. Для него есть отдельный декоратор:

```python
from maxio import MaxBot, Update, Bot

app = MaxBot(os.environ["MAX_TOKEN"])


@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    await bot.send_message("Привет! Напиши /help", chat_id=update.chat_id)
```

!!! tip "Почему не `message`?"
    `bot_started` не несёт объект `Message` — только `update.user`, `update.chat_id`,
    и опционально `update.payload` (deep link). Отвечать нужно через `bot.send_message`.

## Команды

```python
from maxio import Command, Message

@app.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Команды: /help /about")

@app.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer("Бот на фреймворке maxio")
```

## Кнопки

```python
from maxio import InlineKeyboard, Callback, F
from maxio.keyboards import Button

@app.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    kb = (
        InlineKeyboard()
        .row(Button.callback("Да", "yes"), Button.callback("Нет", "no"))
    )
    await message.answer("Выбери:", keyboard=kb)

@app.callback(F.data == "yes")
async def on_yes(callback: Callback) -> None:
    await callback.answer(notification="Ты нажал «Да»!")

@app.callback(F.data == "no")
async def on_no(callback: Callback) -> None:
    await callback.answer(notification="Ты нажал «Нет»!")
```

## Следующие шаги

- [Хэндлеры](handlers.md) — все 11 типов событий
- [Фильтры и F](filters.md) — фильтровать сообщения по тексту, медиа, payload
- [DI — зависимости](di.md) — что можно инжектировать и когда
- [FSM](fsm.md) — многошаговые диалоги
