"""
webhooks_bot.py — управление webhook subscriptions через Bot API.

Показывает: get_subscriptions, subscribe, unsubscribe.

Запуск:
    MAX_TOKEN=<токен> WEBHOOK_URL=https://example.com/max-webhook python examples/webhooks_bot.py
"""

from __future__ import annotations

import logging
import os

from maxio import Bot, Command, MaxBot, Message, UpdateType

logging.basicConfig(level=logging.INFO)

app = MaxBot(os.environ["MAX_TOKEN"])

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")


@app.message(Command("subscriptions"))
async def cmd_subscriptions(message: Message, bot: Bot) -> None:
    result = await bot.get_subscriptions()
    lines = [
        f"{sub.url} ({', '.join(sub.update_types or ['all'])})"
        for sub in result.subscriptions
    ]
    await message.answer("\n".join(lines) or "Подписок нет.")


@app.message(Command("subscribe"))
async def cmd_subscribe(message: Message, bot: Bot) -> None:
    if not WEBHOOK_URL:
        await message.answer("Передай WEBHOOK_URL в окружении перед запуском.")
        return

    await bot.subscribe(
        WEBHOOK_URL,
        update_types=[
            UpdateType.MESSAGE_CREATED.value,
            UpdateType.MESSAGE_CALLBACK.value,
        ],
        secret=WEBHOOK_SECRET,
    )
    await message.answer(f"Подписка создана: {WEBHOOK_URL}")


@app.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message, bot: Bot) -> None:
    if not WEBHOOK_URL:
        await message.answer("Передай WEBHOOK_URL в окружении перед запуском.")
        return

    await bot.unsubscribe(WEBHOOK_URL)
    await message.answer(f"Подписка удалена: {WEBHOOK_URL}")


if __name__ == "__main__":
    app.run()
