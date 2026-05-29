# FSM — диалоги с состоянием

FSM (Finite State Machine) позволяет вести многошаговые диалоги, запоминая, на каком шаге находится пользователь.

## Объявление состояний

```python
from maxio import StatesGroup, State

class Form(StatesGroup):
    waiting_name = State()
    waiting_age  = State()
    waiting_city = State()
```

## FSMContext

`FSMContext` инжектируется в хэндлер по типу. Методы:

```python
await fsm.set_state(Form.waiting_name)   # установить состояние
await fsm.get_state()                    # получить текущее (str или None)
await fsm.clear()                        # сбросить состояние и данные

await fsm.update_data(name="Иван")      # добавить / обновить данные
data = await fsm.get_data()             # получить dict с данными
```

## StateFilter

Фильтрует хэндлер по текущему состоянию пользователя:

```python
from maxio import StateFilter
```

## Пример: анкета

```python
from maxio import MaxBot, Message, FSMContext, Command
from maxio import StatesGroup, State, StateFilter
import os

app = MaxBot(os.environ["MAX_TOKEN"])


class Form(StatesGroup):
    waiting_name = State()
    waiting_age  = State()


@app.message(Command("register"))
async def cmd_register(message: Message, fsm: FSMContext) -> None:
    await fsm.set_state(Form.waiting_name)
    await message.answer("Как тебя зовут?")


@app.message(StateFilter(Form.waiting_name))
async def got_name(message: Message, fsm: FSMContext) -> None:
    await fsm.update_data(name=message.text)
    await fsm.set_state(Form.waiting_age)
    await message.answer("Сколько тебе лет?")


@app.message(StateFilter(Form.waiting_age))
async def got_age(message: Message, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    await fsm.clear()
    await message.answer(f"Записал: {data.get('name', '?')}, {message.text or '?'} лет.")


@app.message(Command("cancel"), StateFilter(Form.waiting_name, Form.waiting_age))
async def cancel(message: Message, fsm: FSMContext) -> None:
    await fsm.clear()
    await message.answer("Отменено.")
```

## Хранилище

По умолчанию используется `MemoryStorage` — хранит состояния в памяти процесса (теряются при перезапуске).

```python
from maxio import MaxBot, MemoryStorage

app = MaxBot(token, storage=MemoryStorage())
```

Своё хранилище — реализуйте протокол `BaseStorage`:

```python
from maxio import BaseStorage, StorageKey

class RedisStorage(BaseStorage):
    async def get_state(self, key: StorageKey) -> str | None: ...
    async def set_state(self, key: StorageKey, state: str | None) -> None: ...
    async def get_data(self, key: StorageKey) -> dict: ...
    async def set_data(self, key: StorageKey, data: dict) -> None: ...
    async def clear(self, key: StorageKey) -> None: ...

app = MaxBot(token, storage=RedisStorage(...))
```

`StorageKey` — `(user_id, chat_id)`.

## StateFilter с несколькими состояниями

```python
@app.message(Command("cancel"), StateFilter(Form.waiting_name, Form.waiting_age))
async def cancel(message: Message, fsm: FSMContext) -> None:
    await fsm.clear()
    await message.answer("Отменено.")
```

Хэндлер сработает в любом из перечисленных состояний.
