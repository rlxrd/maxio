# Changelog

## [0.5.0] — 2026-06-05

### Добавлено

- Методы для управления чатами, закрепами, участниками, администраторами и членством бота.
- Методы webhook subscriptions: `get_subscriptions`, `subscribe`, `unsubscribe`.
- Метод `get_video_info`.
- Экспорт новых типов из `maxio`: `ChatAction`, `ChatMemberRole`, `ChatList`,
  `ChatMember`, `ChatMemberList`, `Subscription`, `SubscriptionList`, `VideoInfo`.
- Примеры: `chat_tools_bot.py`, `media_upload_bot.py`, `webhooks_bot.py`.

### Изменено

- API host: `https://platform-api.max.ru`.
- Авторизация: только `Authorization` header, без `access_token` в query.
- `Bot` стал прямым HTTP-клиентом без `maxio.methods` / `MaxMethod`.
- `get_chats()` возвращает `ChatList` с `chats` и `marker`.
- Маскирование токена в логах всегда включено.
- HTTP client инкапсулирован; внешний `client` больше не часть публичного API.

### Исправлено

- `get_pinned_message()` корректно обрабатывает `{"message": null}`.
- Примеры обновлены под текущий API и `MAX_TOKEN`.
- Upload-flow сверён с официальной двухшаговой схемой.

### Удалено

- Удалены `maxio.methods`, `MaxMethod`, `MaxRequest`.
- Удалены параметры `client` и `mask_token_in_logs` из `Bot`.
- Удалён параметр `mask_token_in_logs` из `MaxBot`.
- Удалён неиспользуемый `_docs.Doc` / `typing.Annotated` metadata layer.

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
