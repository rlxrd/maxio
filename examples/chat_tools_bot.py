"""
chat_tools_bot.py — примеры методов управления чатами.

Показывает: get_chat, get_chats, send_chat_action, pinned messages,
            members/admins lists.

Запуск:
    MAX_TOKEN=<токен> python examples/chat_tools_bot.py
"""

from __future__ import annotations

import logging
import os

from maxio import Bot, ChatAction, Command, MaxBot, Message

logging.basicConfig(level=logging.INFO)

app = MaxBot(os.environ["MAX_TOKEN"])


@app.message(Command("chatinfo"))
async def cmd_chatinfo(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        await message.answer("Эта команда работает только в чате.")
        return

    chat = await bot.get_chat(message.chat_id)
    await message.answer(
        f"Чат: {chat.title or 'без названия'}\n"
        f"ID: {chat.chat_id}\n"
        f"Тип: {chat.type}\n"
        f"Участников: {chat.participants_count or 0}"
    )


@app.message(Command("chats"))
async def cmd_chats(message: Message, bot: Bot) -> None:
    result = await bot.get_chats(count=20)
    lines = [f"{chat.chat_id}: {chat.title or chat.type}" for chat in result.chats]
    await message.answer("\n".join(lines) or "Бот пока не состоит в чатах.")


@app.message(Command("members"))
async def cmd_members(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        await message.answer("Эта команда работает только в чате.")
        return

    result = await bot.get_chat_members(message.chat_id, count=20)
    lines = [
        f"{member.user_id}: {member.name or member.first_name or 'без имени'} ({member.role})"
        for member in result.members
    ]
    await message.answer("\n".join(lines) or "Участники не найдены.")


@app.message(Command("admins"))
async def cmd_admins(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        await message.answer("Эта команда работает только в чате.")
        return

    admins = await bot.get_chat_admins(message.chat_id, count=20)
    lines = [
        f"{admin.user_id}: {admin.name or admin.first_name or 'без имени'} ({admin.role})"
        for admin in admins
    ]
    await message.answer("\n".join(lines) or "Администраторы не найдены.")


@app.message(Command("typing"))
async def cmd_typing(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        return
    await bot.send_chat_action(message.chat_id, ChatAction.TYPING_ON)
    await message.answer("Отправил typing indicator.")


@app.message(Command("pinned"))
async def cmd_pinned(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        await message.answer("Эта команда работает только в чате.")
        return

    pinned = await bot.get_pinned_message(message.chat_id)
    await message.answer(f"Закреплено: {pinned.text}" if pinned else "Закрепа нет.")


@app.message(Command("pin"))
async def cmd_pin(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        await message.answer("Эта команда работает только в чате.")
        return
    if message.link is None or message.link.message is None:
        await message.answer("Ответь командой /pin на сообщение, которое нужно закрепить.")
        return

    await bot.pin_message(message.chat_id, message.link.message.mid)
    await message.answer("Сообщение закреплено.")


@app.message(Command("unpin"))
async def cmd_unpin(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        await message.answer("Эта команда работает только в чате.")
        return

    await bot.unpin_message(message.chat_id)
    await message.answer("Закреп снят.")


if __name__ == "__main__":
    app.run()
