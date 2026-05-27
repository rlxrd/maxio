import logging
import os

from maxio import Bot, Callback, Command, InlineKeyboard, MaxBot, Message, Update
from maxio.keyboards import Button

logging.basicConfig(level=logging.INFO)

app = MaxBot(os.environ["MAX_TOKEN"])


# Синяя кнопка Start шлёт отдельное событие bot_started (без message), а не /start.
@app.bot_started()
async def on_bot_started(update: Update, bot: Bot) -> None:
    keyboard = InlineKeyboard().row(Button.callback("Пинг", "ping"))
    await bot.send_message(
        f"Привет, {update.user.full_name if update.user else 'друг'}!",
        chat_id=update.chat_id,
        keyboard=keyboard,
    )


@app.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer("Это бот на фреймворке maxio!")


@app.callback()
async def on_ping(callback: Callback) -> None:
    await callback.answer(notification="Понг!")          # всплывашка на кнопке
    if callback.message:                                 # + новое сообщение в тот же чат
        await callback.message.answer("Ты нажал кнопку!")


@app.message()
async def echo(message: Message) -> None:
    await message.reply(message.text or "(пустое сообщение)")


if __name__ == "__main__":
    app.run()
