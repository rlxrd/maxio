"""
routers_bot.py — пример модульного бота с несколькими роутерами.

Показывает: разбивка хэндлеров по роутерам, middleware на роутере,
            MaxBot.include_routers, приоритет app > routers.

Запуск:
    MAX_TOKEN=<токен> python examples/routers_bot.py
"""

from __future__ import annotations

import logging
import os

from maxio import (
    Bot,
    Callback,
    CallbackPayload,
    Command,
    F,
    InlineKeyboard,
    MaxBot,
    Message,
    Router,
    Update,
    User,
)
from maxio.keyboards import Button
from maxio.middleware import CallNextOuter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = MaxBot(os.environ["MAX_TOKEN"])


# =============================================================================
# admin роутер — только для администраторов
# =============================================================================

admin = Router()

ADMIN_IDS: set[int] = {int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x}


async def require_admin(call_next: CallNextOuter, user: User | None) -> bool:
    """Пропускает только пользователей из ADMIN_IDS."""
    if not user or user.user_id not in ADMIN_IDS:
        return False
    return await call_next()


admin.outer_middleware(require_admin)


@admin.message(Command("stats"))
async def cmd_stats(message: Message, bot: Bot) -> None:
    me = await bot.get_me()
    await message.answer(f"Бот: @{me.username}\nAdmin IDs: {ADMIN_IDS}")


@admin.message(Command("broadcast"))
async def cmd_broadcast(message: Message) -> None:
    text = (message.text or "").removeprefix("/broadcast").strip()
    if not text:
        await message.answer("Используй: /broadcast <текст>")
        return
    await message.answer(f"[Рассылка]\n{text}")


# =============================================================================
# shop роутер — магазин
# =============================================================================

shop = Router()


@shop.message(Command("shop"))
async def cmd_shop(message: Message) -> None:
    kb = (
        InlineKeyboard()
        .row(
            Button.callback("🍕 Пицца — 500₽", "buy:pizza"),
            Button.callback("🍔 Бургер — 350₽", "buy:burger"),
        )
        .row(Button.callback("🛒 Корзина", "cart"))
    )
    await message.answer("Добро пожаловать в магазин!", keyboard=kb)


@shop.callback(F.data.startswith("buy:"))
async def cb_buy(callback: Callback) -> None:
    item = (callback.payload or "").removeprefix("buy:")
    await callback.answer(notification=f"Добавлено: {item}")
    if callback.message:
        await callback.message.answer(f"✅ {item} добавлен в корзину")


@shop.callback(CallbackPayload("cart"))
async def cb_cart(callback: Callback) -> None:
    await callback.answer(notification="Корзина пуста")


# =============================================================================
# help роутер — справка
# =============================================================================

help_router = Router()


@help_router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/shop — открыть магазин\n"
        "/help — справка\n"
        "/stats — статистика (только для админов)\n"
        "/broadcast — рассылка (только для админов)"
    )


# =============================================================================
# Общие хэндлеры на app (приоритет выше роутеров)
# =============================================================================

@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    if update.chat_id:
        await bot.send_message(
            "Привет! Напиши /help для справки.",
            chat_id=update.chat_id,
        )


@app.message()
async def fallback(message: Message) -> None:
    await message.answer("Не понял. Напиши /help")


# =============================================================================
# Подключаем роутеры: admin → shop → help
# Порядок определяет приоритет (после app)
# =============================================================================

app.include_routers(admin, shop, help_router)


if __name__ == "__main__":
    app.run()
