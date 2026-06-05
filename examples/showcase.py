"""
showcase.py — полный справочник возможностей maxio.

Запуск:
    MAX_TOKEN=<токен> python examples/showcase.py
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from maxio import (
    Bot,
    Callback,
    Command,
    F,
    FSMContext,
    HasMedia,
    InlineKeyboard,
    MaxBot,
    Message,
    Router,
    State,
    StateFilter,
    StatesGroup,
    Update,
    User,
    media,
)
from maxio.enums import Intent, UpdateType, UploadType
from maxio.keyboards import Button
from maxio.middleware import CallNextInner, CallNextOuter, HandlerKwargs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ПРИЛОЖЕНИЕ И РОУТЕРЫ
#
# MaxBot наследует Router — декораторы работают одинаково на MaxBot и Router.
# app обходится первым, затем роутеры в порядке include_routers.
# =============================================================================

app = MaxBot(
    os.environ["MAX_TOKEN"],
    timeout=60.0,  # таймаут HTTP-запросов
)

admin_router = Router()
user_router = Router()

app.include_routers(admin_router, user_router)


# =============================================================================
# MIDDLEWARE
#
# Полный порядок для хэндлера из роутера:
#   app.outer → router.outer → app.inner → router.inner → handler
#
# Outer middleware: оборачивает всю диспетчеризацию.
#   Принимает update + call_next по DI; может прервать цепочку (не вызвать call_next).
#
# Inner middleware: вызывается после выбора хэндлера, до его вызова.
#   Принимает call_next + любые DI-типы (Message, User, Bot и др.).
# =============================================================================


# --- Outer middleware: замер времени ---

class TimingMiddleware:
    async def __call__(self, update: Update, call_next: CallNextOuter) -> bool:
        t = time.monotonic()
        result = await call_next()
        logger.info("[timing] %s → %.3f сек", update.update_type, time.monotonic() - t)
        return result


app.outer_middleware(TimingMiddleware())


# --- Outer middleware: функция, только для message_created ---

async def log_messages(update: Update, call_next: CallNextOuter, user: User | None) -> bool:
    logger.info("[msg] от user_id=%s", user.user_id if user else "?")
    return await call_next()


app.outer_middleware(log_messages, UpdateType.MESSAGE_CREATED)


# --- Outer middleware на роутере: проверка прав ---
# User инжектируется по типу — не нужно читать из update вручную

ADMIN_IDS = {123456789}


async def require_admin(call_next: CallNextOuter, user: User | None) -> bool:
    if not user or user.user_id not in ADMIN_IDS:
        return False
    return await call_next()


admin_router.outer_middleware(require_admin)


# --- Inner middleware: логирование kwargs хэндлера ---
# HandlerKwargs — уже резолвленные аргументы, которые пойдут в хэндлер

async def log_handler_args(call_next: CallNextInner, kwargs: HandlerKwargs) -> None:
    logger.debug("[inner] хэндлер получит: %s", list(kwargs.keys()))
    await call_next()


app.inner_middleware(log_handler_args)


# =============================================================================
# F — MAGIC FILTER
#
# F — ленивый объект для построения фильтров без лишних классов.
# Поддерживает: ==, !=, &, |, ~, .startswith(), .endswith(),
#               .contains(), .in_(), .not_in_()
#
# Шорткаты:
#   F.text      → message.text
#   F.data      → callback.payload
#   F.payload   → update.payload (bot_started deep link)
#   F.photo / F.image → есть фото-вложение
#   F.video, F.audio, F.file / F.document — аналогично
#
# Полный путь тоже работает: F.message.sender.user_id == 5
# =============================================================================

# Примеры ниже используют F как фильтр в декораторах хэндлеров.


# =============================================================================
# ХЭНДЛЕРЫ — ВСЕ ТИПЫ СОБЫТИЙ
# =============================================================================

# --- bot_started: пользователь нажал кнопку «Начать» ---
# Поля: update.user, update.chat_id, update.payload (deep link)

@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    kb = (
        InlineKeyboard()
        .row(Button.callback("Помощь", "help"), Button.callback("О боте", "about"))
        .row(Button.link("Сайт MAX", "https://max.ru"))
    )
    if update.chat_id:
        await bot.send_message("Привет! Выбери действие:", chat_id=update.chat_id, keyboard=kb)


# --- message_created: входящее сообщение ---

@app.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Доступные команды:\n/help — справка\n/about — о боте\n/register — анкета")


@app.message(Command("about"))
async def cmd_about(message: Message, bot: Bot) -> None:
    me = await bot.get_me()
    await message.answer(f"Бот @{me.username} на фреймворке maxio")


# F вместо CallbackPayload и ручных проверок
@app.message(F.text == "да")
async def on_yes(message: Message) -> None:
    await message.answer("Ты сказал «да»!")


@app.message(F.text.in_("стоп", "отмена", "отменить"))
async def on_stop_words(message: Message) -> None:
    await message.answer("Понял, останавливаю.")


@app.message(F.text.startswith("/") & ~F.text.startswith("/start"))
async def unknown_command(message: Message) -> None:
    await message.answer("Неизвестная команда. Напиши /help")


# Несколько фильтров через AND — личный чат и непустой текст
def is_private(update: Update) -> bool:
    return bool(update.message and update.message.recipient.chat_type == "dialog")


@user_router.message(is_private, F.text)
async def echo_private(message: Message) -> None:
    await message.reply(message.text or "")


@app.message()
async def fallback_message(message: Message) -> None:
    await message.answer("Не понял. Напиши /help")


# --- message_edited: пользователь отредактировал сообщение ---

@app.message_edited()
async def on_edit(message: Message) -> None:
    await message.answer(f"Ты отредактировал: «{message.text}»")


# --- message_removed: сообщение удалено ---
# Поля: update.message_id, update.chat_id — объекта Message нет

@app.message_removed()
async def on_removed(update: Update) -> None:
    logger.info("Удалено сообщение %s в чате %s", update.message_id, update.chat_id)


# --- message_callback: нажата inline-кнопка ---

@app.callback(F.data == "help")
async def cb_help(callback: Callback) -> None:
    await callback.answer(notification="Открываю справку…")
    if callback.message:
        await callback.message.answer("Команды: /help /about /register")


@app.callback(F.data == "about")
async def cb_about(callback: Callback, bot: Bot) -> None:
    me = await bot.get_me()
    await callback.answer(notification=f"Бот @{me.username}")


@app.callback(F.data.in_("buy", "sell"))
async def cb_trade(callback: Callback) -> None:
    action = "Покупаю" if callback.payload == "buy" else "Продаю"
    await callback.answer(notification=action)


@app.callback()
async def cb_fallback(callback: Callback) -> None:
    await callback.answer(notification=f"Нажата кнопка: {callback.payload}")


# --- bot_added: бот добавлен в чат или канал ---
# Поля: update.chat_id, update.user (кто добавил), update.is_channel

@app.bot_added()
async def on_bot_added(update: Update, bot: Bot) -> None:
    kind = "канал" if update.is_channel else "чат"
    logger.info("Бот добавлен в %s %s", kind, update.chat_id)
    if update.chat_id and not update.is_channel:
        await bot.send_message("Привет! Я готов к работе.", chat_id=update.chat_id)


# --- bot_removed: бот удалён из чата или канала ---

@app.bot_removed()
async def on_bot_removed(update: Update) -> None:
    logger.info("Бот удалён из чата %s", update.chat_id)


# --- user_added: пользователь добавлен в чат ---
# Поля: update.user (кто добавлен), update.chat_id, update.inviter_id

@app.user_added()
async def on_user_added(update: Update, bot: Bot, user: User | None) -> None:
    if user and update.chat_id:
        await bot.send_message(
            f"Добро пожаловать, {user.full_name}!",
            chat_id=update.chat_id,
        )


# --- user_removed: пользователь покинул или удалён из чата ---
# Поля: update.user (кто ушёл), update.chat_id, update.admin_id (кто выгнал)

@app.user_removed()
async def on_user_removed(update: Update, user: User | None) -> None:
    name = user.full_name if user else "Кто-то"
    logger.info("%s покинул чат %s", name, update.chat_id)


# --- chat_created: создан групповой чат с ботом ---
# Поля: update.chat (объект Chat), update.message_id

@app.chat_created()
async def on_chat_created(update: Update, bot: Bot) -> None:
    if update.chat_id:
        await bot.send_message("Чат создан! Я готов.", chat_id=update.chat_id)


# --- chat_title_changed: изменён заголовок чата ---
# Поля: update.chat_id, update.title (новый), update.user (кто менял)

@app.chat_title_changed()
async def on_title_changed(update: Update) -> None:
    logger.info("Чат %s переименован в «%s»", update.chat_id, update.title)


# =============================================================================
# DI — ВНЕДРЕНИЕ ЗАВИСИМОСТЕЙ
#
# Объявляй в сигнатуре хэндлера только то, что нужно.
# Фреймворк резолвит аргументы по аннотации типа.
#
# Доступно всегда:     Update, Bot, FSMContext
# Для message_*:       Message, User (sender)
# Для callback:        Callback, User
# Для user_added и др.: User (из update.user)
# Для chat_created:    Chat
#
# Optional[X] / X | None — подставляется None если тип недоступен.
# =============================================================================

@user_router.message(Command("me"))
async def cmd_me(message: Message, user: User, bot: Bot) -> None:
    me = await bot.get_me()
    await message.answer(
        f"Ты: {user.full_name} (id={user.user_id})\n"
        f"Я: @{me.username}"
    )


# Optional — безопасно даже если sender не известен
@app.event(UpdateType.MESSAGE_CREATED)
async def log_sender(update: Update, user: User | None) -> None:
    logger.debug("Сообщение от: %s", user.full_name if user else "неизвестен")


# =============================================================================
# КЛАВИАТУРА
# =============================================================================

@user_router.message(Command("keyboard"))
async def cmd_keyboard(message: Message) -> None:
    kb = (
        InlineKeyboard()
        .row(
            Button.callback("✅ Ок", "ok", intent=Intent.POSITIVE),
            Button.callback("❌ Отмена", "cancel", intent=Intent.NEGATIVE),
        )
        .row(Button.callback("Купить", "buy"), Button.callback("Продать", "sell"))
        .row(Button.link("Документация", "https://dev.max.ru"))
        .row(Button.request_contact("📱 Поделиться номером"))
        .row(Button.request_geo_location("📍 Моя геопозиция"))
    )
    await message.answer("Выбери действие:", keyboard=kb)


# =============================================================================
# FSM — КОНЕЧНЫЕ АВТОМАТЫ
# =============================================================================

class Form(StatesGroup):
    waiting_name = State()
    waiting_age = State()


@user_router.message(Command("register"))
async def cmd_register(message: Message, fsm: FSMContext) -> None:
    await fsm.set_state(Form.waiting_name)
    await message.answer("Как тебя зовут?")


@user_router.message(StateFilter(Form.waiting_name))
async def fsm_got_name(message: Message, fsm: FSMContext) -> None:
    await fsm.update_data(name=message.text)
    await fsm.set_state(Form.waiting_age)
    await message.answer("Сколько тебе лет?")


@user_router.message(StateFilter(Form.waiting_age))
async def fsm_got_age(message: Message, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    await fsm.clear()
    await message.answer(f"Записал: {data.get('name', '?')}, {message.text or '?'} лет.")


@user_router.message(Command("cancel"), StateFilter(Form.waiting_name, Form.waiting_age))
async def fsm_cancel(message: Message, fsm: FSMContext) -> None:
    await fsm.clear()
    await message.answer("Отменено.")


# =============================================================================
# МЕДИА
# =============================================================================

@user_router.message(Command("sendphoto"))
async def cmd_send_photo(message: Message, bot: Bot) -> None:
    photo_path = Path("examples/sample.jpg")
    if not photo_path.exists():
        await message.answer("Файл examples/sample.jpg не найден.")
        return
    token = await bot.upload(photo_path, UploadType.IMAGE)
    await message.answer("Держи картинку!", attachments=[media.image(token)])


# F.photo вместо HasMedia("image")
@user_router.message(F.photo)
async def got_photo(message: Message) -> None:
    urls = [p.url for p in message.photos if p.url]
    await message.answer("Фото:\n" + "\n".join(urls or ["—"]))


@user_router.message(F.video)
async def got_video(message: Message) -> None:
    await message.answer(f"Видео получено ({len(message.videos)} шт.)")


@user_router.message(F.file)
async def got_file(message: Message) -> None:
    for f in message.files:
        await message.answer(f"Файл: {f.filename} ({f.size or '?'} байт)")


# HasMedia без аргументов — любое вложение (старый стиль, тоже работает)
@user_router.message(HasMedia())
async def got_any_media(message: Message) -> None:
    types = {a.type for a in message.attachments}
    await message.answer(f"Медиа: {', '.join(sorted(types))}")


# =============================================================================
# ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    app.run()
