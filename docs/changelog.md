# Changelog

## [0.4.0] — 2026-05-29

### Добавлено

- **Все 11 типов событий — именованные декораторы** (`router.py`).
  Новые декораторы: `message_removed`, `chat_created`, `chat_title_changed`,
  `user_added`, `user_removed`, `bot_added`, `bot_removed`.

- **F (MagicFilter)** — `from maxio import F`.
  Шорткаты: `F.text`, `F.data`, `F.photo`/`F.image`, `F.video`, `F.audio`, `F.file`/`F.document`.
  Операторы: `==`, `!=`, `.startswith()`, `.endswith()`, `.contains()`, `.in_()`, `.not_in_()`.
  Комбинаторы: `&`, `|`, `~`.

- **DI в middleware** — `CallNextOuter`, `CallNextInner`, `HandlerKwargs` инжектируются по типу.

- **Optional в DI** — `X | None` подставляет `None` вместо `MaxError`.

### Изменено

- `MaxBot.__init__` — убран `**bot_kwargs`, явные параметры: `storage`, `timeout`, `mask_token_in_logs`.
- `Bot.__init__` — убран `base_url` из публичного API.
- Middleware-сигнатуры: `call_next: Any` → `call_next: CallNextOuter / CallNextInner`.

---

## [0.3.0] — 2026-05-28

- **Роутеры** (`Router`), `include_routers`.
- **Middleware** (outer / inner).
- **FSM**: `StatesGroup`, `State`, `FSMContext`, `StateFilter`, `MemoryStorage`.
- **Медиа**: `Bot.upload()`, `media.image/video/audio/file()`, `HasMedia`.

## [0.2.0] — 2026-05-27

- Маскировка токена в логах (`TokenMaskingFilter`).
- `bot_started()` вместо `startup()`.
- Типы `Callback` и `CallbackQuery` объединены.

## [0.1.0] — 2025-05-27

- Long polling, HTTP-клиент, базовые декораторы, DI, фильтры, клавиатуры.
