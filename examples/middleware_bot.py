"""
middleware_bot.py — примеры outer и inner middleware.

Показывает: замер времени, блокировка пользователей, добавление данных
            через inner middleware, фильтрация по типу апдейта.

Запуск:
    MAX_TOKEN=<токен> python examples/middleware_bot.py
"""

from __future__ import annotations

import logging
import os
import time

from maxio import (
    Bot,
    Command,
    FSMContext,
    MaxBot,
    Message,
    Update,
    User,
)
from maxio.enums import UpdateType
from maxio.middleware import CallNextInner, CallNextOuter, HandlerKwargs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = MaxBot(os.environ["MAX_TOKEN"])

BANNED_IDS: set[int] = set()


# =============================================================================
# OUTER MIDDLEWARE
# Оборачивает всю диспетчеризацию — включая поиск хэндлера.
# Возвращает bool: True = обработано, False = отклонено.
# =============================================================================


# --- Замер времени всех апдейтов ---

async def timing_middleware(update: Update, call_next: CallNextOuter) -> bool:
    t = time.monotonic()
    result = await call_next()
    elapsed = (time.monotonic() - t) * 1000
    logger.info("[%.1fms] %s", elapsed, update.update_type)
    return result


app.outer_middleware(timing_middleware)


# --- Блокировка пользователей ---

async def ban_middleware(call_next: CallNextOuter, user: User | None) -> bool:
    if user and user.user_id in BANNED_IDS:
        logger.warning("Заблокированный пользователь %s", user.user_id)
        return False   # хэндлер не вызовется
    return await call_next()


app.outer_middleware(ban_middleware)


# --- Логирование только сообщений (не колбэков и т.п.) ---

async def log_messages(update: Update, call_next: CallNextOuter, user: User | None) -> bool:
    uid = user.user_id if user else "?"
    text = update.message.text if update.message else ""
    logger.info("[msg] user=%s text=%r", uid, text)
    return await call_next()


app.outer_middleware(log_messages, UpdateType.MESSAGE_CREATED)


# =============================================================================
# INNER MIDDLEWARE
# Вызывается после выбора хэндлера, до его запуска.
# Не возвращает значение. HandlerKwargs — уже резолвленные аргументы.
# =============================================================================


# --- Логирование аргументов хэндлера ---

async def log_handler_kwargs(call_next: CallNextInner, kwargs: HandlerKwargs) -> None:
    logger.debug("[inner] аргументы: %s", list(kwargs.keys()))
    await call_next()


app.inner_middleware(log_handler_kwargs)


# --- Антиспам: не чаще одного сообщения в секунду ---

_last_message: dict[int, float] = {}
RATE_LIMIT = 1.0   # секунд


async def rate_limit(call_next: CallNextInner, user: User | None) -> None:
    if user:
        now = time.monotonic()
        last = _last_message.get(user.user_id, 0.0)
        if now - last < RATE_LIMIT:
            return   # хэндлер не вызовется
        _last_message[user.user_id] = now
    await call_next()


app.inner_middleware(rate_limit)


# =============================================================================
# ХЭНДЛЕРЫ
# =============================================================================

@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    if update.chat_id:
        await bot.send_message(
            "Привет! Попробуй /ban и /unban чтобы увидеть middleware в действии.",
            chat_id=update.chat_id,
        )


@app.message(Command("ban"))
async def cmd_ban(message: Message, user: User) -> None:
    BANNED_IDS.add(user.user_id)
    await message.answer(f"Пользователь {user.user_id} заблокирован")


@app.message(Command("unban"))
async def cmd_unban(message: Message, user: User) -> None:
    BANNED_IDS.discard(user.user_id)
    await message.answer(f"Пользователь {user.user_id} разблокирован")


@app.message(Command("me"))
async def cmd_me(message: Message, user: User, fsm: FSMContext) -> None:
    state = await fsm.get_state()
    await message.answer(
        f"ID: {user.user_id}\n"
        f"Имя: {user.full_name}\n"
        f"Состояние FSM: {state or 'нет'}"
    )


@app.message()
async def echo(message: Message) -> None:
    await message.reply(message.text or "")


if __name__ == "__main__":
    app.run()
