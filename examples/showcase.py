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
    CallbackPayload,
    Command,
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
from maxio.middleware import CallNextInner, CallNextOuter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# ПРИЛОЖЕНИЕ
# =============================================================================

app = MaxBot(os.environ.get("MAX_TOKEN", "TOKEN"))

# =============================================================================
# РОУТЕРЫ
# Декораторы message/callback/... работают одинаково на MaxBot и Router.
# app обходится первым, затем роутеры в порядке include_routers.
# =============================================================================

admin_router = Router()
user_router = Router()

app.include_routers(admin_router, user_router)

# =============================================================================
# MIDDLEWARE
# Middleware — callable (класс с __call__ или функция).
# Регистрируется на app или router через outer_middleware / inner_middleware.
#
# Полный порядок для хэндлера из роутера:
#   app.outer → router.outer → app.inner → router.inner → handler()
# =============================================================================

# --- Outer middleware: оборачивает всю диспетчеризацию ---
# Получает: (update, call_next) → bool
# Может прервать обработку (не вызвать call_next) или модифицировать апдейт.


class TimingMiddleware:
    """Замеряет время обработки каждого апдейта."""

    async def __call__(self, update: Update, call_next: CallNextOuter) -> bool:
        t = time.monotonic()
        result = await call_next()
        logger.info("[timing] %s → %.3f сек", update.update_type, time.monotonic() - t)
        return result


# Регистрация на app — срабатывает для всех апдейтов
app.outer_middleware(TimingMiddleware())


# Функция тоже подходит — не обязательно класс
async def log_updates(update: Update, call_next: CallNextOuter) -> bool:
    logger.info("[log] входящий апдейт: %s", update.update_type)
    return await call_next()


# Только для сообщений
app.outer_middleware(log_updates, UpdateType.MESSAGE_CREATED)


# --- Outer middleware на роутере ---
# Срабатывает только если хэндлер принадлежит этому роутеру

ADMIN_IDS = {123456789}


async def require_admin(update: Update, call_next: CallNextOuter) -> bool:
    user = (
        (update.message and update.message.sender)
        or (update.callback and update.callback.user)
        or update.user
    )
    if not user or user.user_id not in ADMIN_IDS:
        return False
    return await call_next()


admin_router.outer_middleware(require_admin)


# --- Inner middleware: вызывается после выбора хэндлера ---
# Получает: (handler_fn, kwargs, call_next) → None
# kwargs — уже резолвленные аргументы хэндлера (можно читать и изменять).


class InjectDbUser:
    """Добавляет данные о пользователе из «базы» в kwargs."""

    async def __call__(
        self, handler: object, kwargs: dict[str, object], call_next: CallNextInner
    ) -> None:
        message: Message | None = kwargs.get("message")  # type: ignore[assignment]
        if message and message.sender:
            # имитация запроса к БД
            kwargs["db_user"] = {"id": message.sender.user_id, "premium": False}
        await call_next()


app.inner_middleware(InjectDbUser())

# =============================================================================
# ФИЛЬТРЫ
# Фильтр — объект с методом async check(update) -> bool
#           или простая функция (sync/async) update -> bool.
# Несколько фильтров в декораторе объединяются как AND.
# =============================================================================


# --- Встроенные фильтры ---

# Command: совпадает если сообщение начинается с /команды
# CallbackPayload: совпадает если payload кнопки равен одному из значений


# --- Кастомный фильтр через класс (Protocol Filter) ---

class IsPrivateChat:
    """Пропускает только личные чаты (не группы)."""

    async def check(self, update: Update) -> bool:
        if update.message and update.message.recipient:
            return update.message.recipient.chat_type == "dialog"
        return False


# --- Кастомный фильтр через функцию ---

def has_text(update: Update) -> bool:
    """Пропускает только сообщения с непустым текстом."""
    return bool(update.message and update.message.text)


# --- Кастомный фильтр async-функцией ---

async def not_bot(update: Update) -> bool:
    """Пропускает только сообщения от живых пользователей."""
    if update.message and update.message.sender:
        return not update.message.sender.is_bot
    return True


# =============================================================================
# ХЭНДЛЕРЫ — ТИПЫ СОБЫТИЙ
# =============================================================================

# --- bot_started: пользователь нажал кнопку «Начать» ---

@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    kb = (
        InlineKeyboard()
        .row(Button.callback("Помощь", "help"), Button.callback("О боте", "about"))
        .row(Button.link("Сайт MAX", "https://max.ru"))
    )
    chat_id = update.chat_id
    if chat_id:
        await bot.send_message("Привет! Выбери действие:", chat_id=chat_id, keyboard=kb)


# --- message: входящее сообщение ---

@app.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Доступные команды:\n/help — эта справка\n/about — о боте")


@app.message(Command("about"))
async def cmd_about(message: Message, bot: Bot) -> None:
    me = await bot.get_me()
    await message.answer(f"Я бот @{me.username}, версия maxio v0.3")


# Несколько фильтров одновременно (AND): личный чат + непустой текст
@user_router.message(IsPrivateChat(), has_text, not_bot)
async def echo_private(message: Message) -> None:
    await message.reply(message.text or "")


# Хэндлер без фильтров — ловит всё остальное (fallback)
@app.message()
async def fallback_message(message: Message) -> None:
    await message.answer("Не понял команду. Напиши /help")


# --- message_edited: пользователь отредактировал сообщение ---

@app.message_edited()
async def on_edit(message: Message) -> None:
    await message.answer(f"Ты отредактировал сообщение: «{message.text}»")


# --- callback: нажатие inline-кнопки ---

@app.callback(CallbackPayload("help"))
async def cb_help(callback: Callback) -> None:
    # answer() — всплывающее уведомление на кнопке
    await callback.answer(notification="Открываю справку…")
    if callback.message:
        await callback.message.answer("Доступные команды:\n/help\n/about")


@app.callback(CallbackPayload("about"))
async def cb_about(callback: Callback, bot: Bot) -> None:
    me = await bot.get_me()
    await callback.answer(notification=f"Бот @{me.username}")


# Fallback для всех остальных callback
@app.callback()
async def cb_fallback(callback: Callback) -> None:
    await callback.answer(notification=f"Нажата кнопка: {callback.payload}")


# --- event: произвольные типы апдейтов (низкоуровневый хэндлер) ---

@app.event(UpdateType.BOT_ADDED, UpdateType.BOT_REMOVED)
async def on_bot_membership(update: Update) -> None:
    action = "добавлен в" if update.update_type == UpdateType.BOT_ADDED else "удалён из"
    logger.info("Бот %s чат %s", action, update.chat_id)


# event без аргументов — ловит вообще всё (используй осторожно)
# @app.event()
# async def catch_all(update: Update) -> None:
#     logger.debug("Неизвестный апдейт: %s", update.update_type)


# =============================================================================
# DI — внедрение зависимостей по аннотациям типов
# Доступные типы в хэндлере:
#   Update  — всегда
#   Bot     — всегда (HTTP-клиент)
#   Message — для message_created / message_edited / callback
#   Callback — для message_callback
#   User    — отправитель / инициатор
#   Chat    — для bot_added / bot_removed и др.
# =============================================================================

@user_router.message(Command("me"))
async def cmd_me(message: Message, user: User, bot: Bot) -> None:
    me = await bot.get_me()
    await message.answer(
        f"Ты: {user.full_name} (id={user.user_id})\n"
        f"Я: @{me.username}"
    )


# =============================================================================
# КЛАВИАТУРА
# InlineKeyboard строится цепочкой .row() / .add().
# Button.*  — фабрики кнопок разных типов.
# =============================================================================

@user_router.message(Command("keyboard"))
async def cmd_keyboard(message: Message, bot: Bot) -> None:
    kb = (
        InlineKeyboard()
        # row() — новый ряд из переданных кнопок
        .row(
            Button.callback("✅ Ок", "ok", intent=Intent.POSITIVE),
            Button.callback("❌ Отмена", "cancel", intent=Intent.NEGATIVE),
        )
        # add() — добавить кнопки в текущий ряд
        .row(Button.link("Документация", "https://dev.max.ru"))
        .row(Button.request_contact("📱 Поделиться номером"))
        .row(Button.request_geo_location("📍 Моя геопозиция"))
    )
    if message.recipient and message.recipient.chat_id:
        await bot.send_message(
            "Выбери действие:",
            chat_id=message.recipient.chat_id,
            keyboard=kb,
        )


# =============================================================================
# FSM — конечные автоматы (диалоги с состоянием)
#
# Определяем группу состояний через StatesGroup.
# Каждое поле-класса State получает ключ "<ИмяГруппы>:<имя_поля>" автоматически.
#
# FSMContext инжектируется в хэндлер по типу аннотации.
# StateFilter используется как обычный фильтр — проверяет текущее состояние.
#
# По умолчанию MaxBot хранит состояния в памяти (MemoryStorage).
# Для многопроцессного деплоя подключи Redis-storage (не входит в ядро).
# =============================================================================


class Form(StatesGroup):
    waiting_name = State()
    waiting_age = State()


# --- Начало диалога ---
@user_router.message(Command("register"))
async def cmd_register(message: Message, fsm: FSMContext) -> None:
    await fsm.set_state(Form.waiting_name)
    await message.answer("Как тебя зовут?")


# --- Шаг 1: принять имя ---
@user_router.message(StateFilter(Form.waiting_name))
async def fsm_got_name(message: Message, fsm: FSMContext) -> None:
    await fsm.update_data(name=message.text)
    await fsm.set_state(Form.waiting_age)
    await message.answer("Сколько тебе лет?")


# --- Шаг 2: принять возраст и завершить ---
@user_router.message(StateFilter(Form.waiting_age))
async def fsm_got_age(message: Message, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    name = data.get("name", "?")
    age = message.text or "?"
    await fsm.clear()
    await message.answer(f"Записал: {name}, {age} лет. Готово!")


# --- Отмена из любого состояния ---
@user_router.message(Command("cancel"), StateFilter(Form.waiting_name, Form.waiting_age))
async def fsm_cancel(message: Message, fsm: FSMContext) -> None:
    await fsm.clear()
    await message.answer("Регистрация отменена.")


# =============================================================================
# МЕДИА — загрузка и отправка файлов, получение вложений
#
# Загрузка — двухшаговый процесс:
#   1. bot.upload(file, UploadType.IMAGE) → строковый токен
#   2. Передать токен через media.image(token) в параметр attachments
#
# Получение — Message.photos / .videos / .audio / .files возвращают
# типизированные payload-объекты с полями token, url, filename, size и др.
#
# HasMedia(*types) — фильтр по наличию вложений нужных типов.
# =============================================================================


# --- Отправить картинку из файла ---
@user_router.message(Command("sendphoto"))
async def cmd_send_photo(message: Message, bot: Bot) -> None:
    # Принимает bytes, IO[bytes] или Path
    photo_path = Path("examples/sample.jpg")
    if not photo_path.exists():
        await message.answer("Файл examples/sample.jpg не найден — добавь его для теста.")
        return
    token = await bot.upload(photo_path, UploadType.IMAGE)
    await message.answer(
        "Держи картинку!",
        attachments=[media.image(token)],
    )


# --- Пересылка полученного файла ---
@user_router.message(HasMedia("file"))
async def echo_file(message: Message) -> None:
    for f in message.files:
        await message.answer(
            f"Получил файл «{f.filename}» "
            f"({f.size or '?'} байт). "
            f"URL: {f.url}"
        )


# --- Получить фото и показать URL ---
@user_router.message(HasMedia("image"))
async def got_photo(message: Message) -> None:
    urls = [p.url for p in message.photos if p.url]
    await message.answer("Фото получены:\n" + "\n".join(urls or ["—"]))


# --- HasMedia без аргументов — любое вложение ---
@user_router.message(HasMedia())
async def got_any_media(message: Message) -> None:
    types = {a.type for a in message.attachments}
    await message.answer(f"Получено медиа: {', '.join(sorted(types))}")


# =============================================================================
# ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    app.run()
