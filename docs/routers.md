# Роутеры

`Router` — отдельный реестр хэндлеров. Используется для разбивки бота на модули.

## Создание и подключение

```python
import os
from maxio import MaxBot, Router

app = MaxBot(os.environ["MAX_TOKEN"])

admin = Router()
users = Router()

app.include_routers(admin, users)
```

`MaxBot` сам является роутером — API одинаков на обоих уровнях.

## Хэндлеры на роутере

```python
@admin.message(Command("ban"))
async def ban(message: Message) -> None:
    await message.answer("Готово.")

@users.message(Command("profile"))
async def profile(message: Message, user: User) -> None:
    await message.answer(f"Профиль: {user.full_name}")
```

Хэндлеры обходятся в порядке: сначала `app`, затем роутеры в порядке `include_routers`.

## Middleware на роутере

Middleware роутера срабатывает только если хэндлер принадлежит этому роутеру:

```python
ADMIN_IDS = {123456789}

async def require_admin(call_next: CallNextOuter, user: User | None) -> bool:
    if not user or user.user_id not in ADMIN_IDS:
        return False
    return await call_next()

admin.outer_middleware(require_admin)
```

Хэндлеры из `users` роутера это middleware не увидят.

## Разбивка по файлам

Типичный layout проекта:

```
bot.py          — создание app, include_routers, запуск
handlers/
  admin.py      — admin = Router() + хэндлеры
  users.py      — users = Router() + хэндлеры
  shop.py       — shop = Router() + хэндлеры
```

```python
# handlers/admin.py
from maxio import Router, Message, Command

admin = Router()

@admin.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    await message.answer("Статистика: ...")
```

```python
# bot.py
import os
from maxio import MaxBot
from handlers.admin import admin
from handlers.users import users

app = MaxBot(os.environ["MAX_TOKEN"])
app.include_routers(admin, users)

if __name__ == "__main__":
    app.run()
```
