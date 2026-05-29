# Фильтры и F

Фильтр — это условие для хэндлера. Хэндлер вызывается только если все фильтры прошли.

## F — Magic Filter

`F` — ленивый объект для построения фильтров без отдельных классов.

```python
from maxio import F
```

### Шорткаты

Самые частые поля доступны напрямую через `F`:

| Выражение | Что проверяет |
|---|---|
| `F.text` | `update.message.text` (truthy) |
| `F.data` | `update.callback.payload` (truthy) |
| `F.payload` | `update.payload` (deep link в `bot_started`) |
| `F.photo` / `F.image` | есть вложение типа `image` |
| `F.video` | есть вложение типа `video` |
| `F.audio` | есть вложение типа `audio` |
| `F.file` / `F.document` | есть вложение типа `file` |

```python
@app.message(F.text)          # любое сообщение с текстом
@app.message(F.photo)         # сообщение с фото
@app.callback(F.data)         # колбэк с любым payload
```

### Операторы сравнения

```python
F.text == "да"               # точное совпадение
F.text != "нет"              # неравенство
F.data.in_("buy", "sell")    # входит в список
F.data.not_in_("x", "y")    # не входит в список
F.text.startswith("/")       # начинается с
F.text.endswith("!")         # заканчивается на
F.text.contains("ключ")      # содержит подстроку
```

### Комбинаторы

```python
F.text & F.photo             # AND — текст и фото
F.text | F.data              # OR — текст или callback data
~F.photo                     # NOT — нет фото
```

```python
# Неизвестная команда (начинается с / но не /start)
@app.message(F.text.startswith("/") & ~F.text.startswith("/start"))
async def unknown_cmd(message: Message) -> None:
    await message.answer("Неизвестная команда. /help")
```

### Полный путь

```python
# Любое поле через цепочку атрибутов
F.message.sender.user_id == 5
F.callback.payload
```

---

## Command

Фильтр по команде (текст начинается с `/команда`):

```python
from maxio import Command

@app.message(Command("help"))
async def cmd_help(message: Message) -> None: ...

@app.message(Command("start"))
async def cmd_start(message: Message) -> None: ...
```

!!! note "Кнопка «Начать» ≠ /start"
    Синяя кнопка Start в MAX шлёт событие `bot_started`, а не текст `/start`.
    Используйте `@app.bot_started()` для обработки кнопки Start.

---

## HasMedia

Фильтр по наличию вложения определённого типа:

```python
from maxio import HasMedia

@app.message(HasMedia("image"))
async def got_photo(message: Message) -> None: ...

@app.message(HasMedia("video"))
async def got_video(message: Message) -> None: ...

@app.message(HasMedia())  # любое вложение
async def got_any(message: Message) -> None: ...
```

`F.photo` / `F.video` / `F.file` — сокращённый синтаксис для `HasMedia`.

---

## Произвольная функция

Любой callable `(Update) -> bool` работает как фильтр:

```python
def is_private(update: Update) -> bool:
    return bool(update.message and update.message.recipient.chat_type == "dialog")

@app.message(is_private, F.text)
async def echo_private(message: Message) -> None:
    await message.reply(message.text or "")
```

---

## StateFilter

Фильтр по текущему состоянию FSM. Подробнее — в разделе [FSM](fsm.md).

```python
from maxio import StateFilter

@app.message(StateFilter(Form.waiting_name))
async def got_name(message: Message, fsm: FSMContext) -> None: ...
```

---

## Несколько фильтров — AND

Все фильтры в декораторе объединяются как AND:

```python
@app.message(Command("buy"), is_private, F.text)
async def buy(message: Message) -> None: ...
```
