# Клавиатуры

maxio поддерживает inline-клавиатуры MAX Bot API.

## InlineKeyboard

```python
from maxio import InlineKeyboard
from maxio.keyboards import Button

kb = (
    InlineKeyboard()
    .row(Button.callback("Да", "yes"), Button.callback("Нет", "no"))
    .row(Button.link("Сайт", "https://example.com"))
)

await message.answer("Выбери:", keyboard=kb)
```

`.row()` добавляет строку кнопок. Несколько кнопок в одной строке — перечисляйте через запятую.

## Типы кнопок

### Button.callback

Кнопка, нажатие которой шлёт событие `message_callback`:

```python
Button.callback("Текст", "payload")
Button.callback("Купить", "buy", intent=Intent.POSITIVE)
Button.callback("Отмена", "cancel", intent=Intent.NEGATIVE)
```

`intent` влияет на цвет кнопки (`POSITIVE` — зелёный, `NEGATIVE` — красный).

### Button.link

Кнопка-ссылка, открывает URL:

```python
Button.link("Документация", "https://dev.max.ru")
Button.link("Наш сайт", "https://example.com")
```

### Button.request_contact

Запрашивает номер телефона пользователя:

```python
Button.request_contact("📱 Поделиться номером")
```

### Button.request_geo_location

Запрашивает геолокацию:

```python
Button.request_geo_location("📍 Моя геопозиция")
```

## Пример: меню

```python
from maxio.enums import Intent

@app.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    kb = (
        InlineKeyboard()
        .row(
            Button.callback("✅ Купить", "buy", intent=Intent.POSITIVE),
            Button.callback("❌ Отмена", "cancel", intent=Intent.NEGATIVE),
        )
        .row(Button.callback("О нас", "about"), Button.callback("Помощь", "help"))
        .row(Button.link("Наш сайт", "https://example.com"))
    )
    await message.answer("Главное меню:", keyboard=kb)


@app.callback(F.data == "buy")
async def on_buy(callback: Callback) -> None:
    await callback.answer(notification="Оформляю заказ…")

@app.callback(F.data == "cancel")
async def on_cancel(callback: Callback) -> None:
    await callback.answer(notification="Отменено")
    if callback.message:
        await callback.message.answer("Действие отменено.")
```

## Обработка нажатий

`callback.answer()` — обязательно вызвать, иначе кнопка будет «зависать»:

```python
@app.callback()
async def cb_handler(callback: Callback) -> None:
    await callback.answer(notification="Готово!")
    # или без уведомления:
    await callback.answer()
```

`callback.payload` — строка payload, переданная в `Button.callback`.
