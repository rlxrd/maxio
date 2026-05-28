from __future__ import annotations

from conftest import message_created
from maxio import (
    FSMContext,
    MaxBot,
    MemoryStorage,
    Message,
    State,
    StateFilter,
    StatesGroup,
    Update,
)
from maxio.fsm.storage import StorageKey

# ---------------------------------------------------------------------------
# MemoryStorage
# ---------------------------------------------------------------------------

async def test_memory_storage_state() -> None:
    storage = MemoryStorage()
    key = StorageKey(user_id=1, chat_id=10)

    assert await storage.get_state(key) is None
    await storage.set_state(key, "Form:name")
    assert await storage.get_state(key) == "Form:name"
    await storage.set_state(key, None)
    assert await storage.get_state(key) is None


async def test_memory_storage_data() -> None:
    storage = MemoryStorage()
    key = StorageKey(user_id=1, chat_id=10)

    assert await storage.get_data(key) == {}
    await storage.set_data(key, {"name": "Иван"})
    assert await storage.get_data(key) == {"name": "Иван"}


async def test_memory_storage_clear() -> None:
    storage = MemoryStorage()
    key = StorageKey(user_id=1, chat_id=10)

    await storage.set_state(key, "some_state")
    await storage.set_data(key, {"x": 1})
    await storage.clear(key)
    assert await storage.get_state(key) is None
    assert await storage.get_data(key) == {}


async def test_memory_storage_isolated_keys() -> None:
    storage = MemoryStorage()
    key1 = StorageKey(user_id=1, chat_id=10)
    key2 = StorageKey(user_id=2, chat_id=10)

    await storage.set_state(key1, "state_a")
    assert await storage.get_state(key2) is None


# ---------------------------------------------------------------------------
# State / StatesGroup
# ---------------------------------------------------------------------------

class Form(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


def test_state_key_format() -> None:
    assert Form.waiting_name.key == "Form:waiting_name"
    assert Form.waiting_phone.key == "Form:waiting_phone"


def test_states_are_distinct() -> None:
    assert Form.waiting_name.key != Form.waiting_phone.key


# ---------------------------------------------------------------------------
# FSMContext
# ---------------------------------------------------------------------------

async def test_fsm_context_set_get_state() -> None:
    storage = MemoryStorage()
    key = StorageKey(user_id=1, chat_id=10)
    ctx = FSMContext(storage, key)

    assert await ctx.get_state() is None
    await ctx.set_state(Form.waiting_name)
    assert await ctx.get_state() == "Form:waiting_name"


async def test_fsm_context_set_state_string() -> None:
    storage = MemoryStorage()
    ctx = FSMContext(storage, StorageKey(user_id=1, chat_id=None))

    await ctx.set_state("custom:state")
    assert await ctx.get_state() == "custom:state"


async def test_fsm_context_update_data() -> None:
    storage = MemoryStorage()
    ctx = FSMContext(storage, StorageKey(user_id=1, chat_id=10))

    await ctx.update_data(name="Иван")
    await ctx.update_data(phone="+7999")
    data = await ctx.get_data()
    assert data == {"name": "Иван", "phone": "+7999"}


async def test_fsm_context_clear() -> None:
    storage = MemoryStorage()
    ctx = FSMContext(storage, StorageKey(user_id=1, chat_id=10))

    await ctx.set_state(Form.waiting_name)
    await ctx.update_data(name="Иван")
    await ctx.clear()
    assert await ctx.get_state() is None
    assert await ctx.get_data() == {}


# ---------------------------------------------------------------------------
# StateFilter
# ---------------------------------------------------------------------------

async def test_state_filter_matches() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(StateFilter(Form.waiting_name))
    async def handler(message: Message) -> None:
        calls.append("matched")

    update = Update.model_validate(message_created())

    # Устанавливаем состояние перед вызовом
    key = StorageKey(user_id=5, chat_id=10)
    await app._storage.set_state(key, Form.waiting_name.key)

    await app.feed_update(update)
    assert calls == ["matched"]
    await app.bot.aclose()


async def test_state_filter_no_match() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(StateFilter(Form.waiting_phone))
    async def handler(message: Message) -> None:
        calls.append("matched")

    update = Update.model_validate(message_created())
    # Состояние не установлено — фильтр не пройдёт
    await app.feed_update(update)
    assert calls == []
    await app.bot.aclose()


async def test_state_filter_multiple_states() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(StateFilter(Form.waiting_name, Form.waiting_phone))
    async def handler(message: Message) -> None:
        calls.append("matched")

    key = StorageKey(user_id=5, chat_id=10)
    await app._storage.set_state(key, Form.waiting_phone.key)

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["matched"]
    await app.bot.aclose()


# ---------------------------------------------------------------------------
# Интеграция: FSMContext инжектируется в хэндлер
# ---------------------------------------------------------------------------

async def test_fsm_context_injected_into_handler() -> None:
    app = MaxBot("TOKEN")
    received: list[FSMContext] = []

    @app.message()
    async def handler(message: Message, state: FSMContext) -> None:
        received.append(state)

    await app.feed_update(Update.model_validate(message_created()))
    assert len(received) == 1
    assert isinstance(received[0], FSMContext)
    await app.bot.aclose()


async def test_fsm_dialog_flow() -> None:
    """Полный сценарий: /start → ввод имени → ввод телефона → финиш."""
    app = MaxBot("TOKEN")
    results: list[str] = []

    @app.message(StateFilter(Form.waiting_name))
    async def got_name(message: Message, state: FSMContext) -> None:
        await state.update_data(name=message.text)
        await state.set_state(Form.waiting_phone)
        results.append(f"name:{message.text}")

    @app.message(StateFilter(Form.waiting_phone))
    async def got_phone(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        results.append(f"phone:{message.text}:name_was:{data['name']}")
        await state.clear()

    key = StorageKey(user_id=5, chat_id=10)

    # Шаг 1: нет состояния — ни один хэндлер не сработает
    await app.feed_update(Update.model_validate(message_created("привет")))
    assert results == []

    # Шаг 2: ставим состояние waiting_name, шлём имя
    await app._storage.set_state(key, Form.waiting_name.key)
    await app.feed_update(Update.model_validate(message_created("Иван")))
    assert results == ["name:Иван"]

    # Шаг 3: состояние теперь waiting_phone, шлём телефон
    await app.feed_update(Update.model_validate(message_created("+79991234567")))
    assert results == ["name:Иван", "phone:+79991234567:name_was:Иван"]

    # Шаг 4: состояние сброшено — хэндлеры снова не сработают
    await app.feed_update(Update.model_validate(message_created("ещё")))
    assert len(results) == 2

    await app.bot.aclose()


async def test_custom_storage_passed_to_maxbot() -> None:
    custom = MemoryStorage()
    app = MaxBot("TOKEN", storage=custom)
    assert app._storage is custom
    await app.bot.aclose()
