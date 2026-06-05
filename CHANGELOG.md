# Changelog

## [Unreleased]

## [0.5.0] — 2026-06-05

### Добавлено

- **Расширено покрытие MAX Bot API**:
  - чаты: `get_chat`, `get_chat_by_link`, `update_chat`, `delete_chat`, `send_chat_action`
  - закрепы: `get_pinned_message`, `pin_message`, `unpin_message`
  - участники: `get_chat_members`, `add_chat_members`, `remove_chat_member`
  - администраторы: `get_chat_admins`, `add_chat_admin`, `remove_chat_admin`
  - членство бота: `get_bot_chat_membership`, `leave_chat`
  - webhooks: `get_subscriptions`, `subscribe`, `unsubscribe`
  - медиа: `get_video_info`
- **Новые публичные типы и enum'ы** экспортируются из `maxio`:
  `ChatAction`, `ChatMemberRole`, `ChatList`, `ChatMember`, `ChatMemberList`,
  `Subscription`, `SubscriptionList`, `VideoInfo`.
- **Новые примеры**:
  - `examples/chat_tools_bot.py` — управление чатами, участниками, админами и закрепами
  - `examples/media_upload_bot.py` — загрузка файлов и обработка входящих медиа
  - `examples/webhooks_bot.py` — управление webhook subscriptions

### Изменено

- **Авторизация переведена на header-only**: токен больше не передаётся в query string,
  все запросы используют `Authorization`.
- **Официальный API host обновлён** с `https://botapi.max.ru` на
  `https://platform-api.max.ru`.
- **`Bot` стал проще**: HTTP-запросы снова собираются напрямую внутри `Bot`, без
  отдельного method-object слоя.
- **`Bot.get_chats()` теперь возвращает `ChatList`**, чтобы сохранить `marker`
  для пагинации.
- **Маскирование токена в логах всегда включено**. Публичный переключатель больше
  не нужен: фильтр дешёвый и защищает `Authorization`/чувствительные URL в debug-логах.
- **HTTP client инкапсулирован**: пользовательский API больше не принимает внешний
  `httpx.AsyncClient`.
- Примеры обновлены под текущий API и используют `MAX_TOKEN` из окружения.

### Исправлено

- `get_pinned_message()` теперь корректно разбирает официальный ответ
  `{"message": Message | null}` и возвращает `None`, если закрепа нет.
- Callback/FSM context теперь корректнее выбирает пользователя для callback update.
- Upload-flow проверен по официальной документации: сохраняется двухшаговая схема
  `POST /uploads?type=...` → multipart upload на выданный URL.
- Убрана неактуальная документация по `add_chat_admin(..., alias=...)`.

### Удалено

- Удалён пакет `maxio.methods` и публичный `MaxMethod`/`MaxRequest` API.
  Фреймворк оставляет один основной стиль: `await bot.send_message(...)`,
  `await bot.get_chat(...)` и т.д.
- Удалён служебный `_docs.Doc`/`typing.Annotated` слой для параметров: он не
  использовался runtime'ом или генерацией документации и усложнял сигнатуры.
- Удалены публичные параметры `client` и `mask_token_in_logs` из `Bot`.
- Удалён параметр `mask_token_in_logs` из `MaxBot`.

## [0.4.0] — 2026-05-29

### Добавлено

- **Все 11 типов событий — именованные декораторы** (`router.py`).
  Ранее 7 типов были доступны только через `@app.event(...)`. Теперь каждый тип
  имеет отдельный декоратор:
  - `@app.message_removed()` — сообщение удалено (`update.message_id`, `update.chat_id`)
  - `@app.chat_created()` — создан групповой чат (`update.chat`, `update.message_id`)
  - `@app.chat_title_changed()` — изменён заголовок (`update.title`, `update.user`)
  - `@app.user_added()` — пользователь добавлен (`update.user`, `update.inviter_id`)
  - `@app.user_removed()` — пользователь удалён (`update.user`, `update.admin_id`)
  - `@app.bot_added()` — бот добавлен в чат/канал (`update.user`, `update.is_channel`)
  - `@app.bot_removed()` — бот удалён из чата/канала (`update.user`, `update.is_channel`)

- **F (MagicFilter)** — `src/maxio/magic.py`, экспортируется как `from maxio import F`.
  Ленивый объект для построения фильтров-выражений без отдельных классов.
  - Шорткаты: `F.text`, `F.data`, `F.payload`, `F.photo`/`F.image`, `F.video`, `F.audio`, `F.file`/`F.document`
  - Операторы: `==`, `!=`, `.startswith()`, `.endswith()`, `.contains()`, `.in_()`, `.not_in_()`
  - Комбинаторы: `&` (AND), `|` (OR), `~` (NOT)
  - Полный путь: `F.message.sender.user_id == 5`

- **DI в middleware** — middleware теперь получает аргументы через тот же механизм, что и хэндлеры.
  `CallNextOuter` и `CallNextInner` стали реальными инжектируемыми классами (раньше — type aliases).
  `HandlerKwargs` — новый инжектируемый тип для inner middleware: словарь уже резолвленных
  аргументов хэндлера. Все три экспортируются из `maxio.middleware` и из `maxio`.

  ```python
  # Раньше
  async def mw(update: Update, call_next: Any) -> bool: ...
  async def mw(handler: Any, kwargs: Any, call_next: Any) -> None: ...

  # Теперь
  async def mw(update: Update, call_next: CallNextOuter, user: User | None) -> bool: ...
  async def mw(call_next: CallNextInner, kwargs: HandlerKwargs, message: Message) -> None: ...
  ```

- **Optional в DI** — резолвер (`injection.py`) понимает `X | None` и `Optional[X]`.
  Если тип недоступен для данного апдейта — подставляется `None` вместо `MaxError`.

  ```python
  @app.bot_started()
  async def on_start(update: Update, message: Message | None) -> None:
      # message == None, bot_started не несёт объект Message
      ...
  ```

### Изменено

- **`MaxBot.__init__`** — убран `**bot_kwargs: Any`, параметры явные и keyword-only:
  `storage`, `timeout`, `mask_token_in_logs`. Убран `base_url` — адрес API фиксирован
  (`https://botapi.max.ru`) и не должен меняться пользователем.
- **`Bot.__init__`** — аналогично убран `base_url` из публичного API.
- Примеры (`echo_bot.py`, `showcase.py`) переписаны под v0.4: новые декораторы,
  `F` вместо `CallbackPayload`, обновлённые сигнатуры middleware.

## [0.3.0] — 2026-05-28

### Добавлено
- **Роутеры** (`Router`): разбивка хэндлеров по файлам через `app.include_routers(r1, r2, ...)`.
  `MaxBot` наследует `Router` — API одинаков на обоих уровнях.
- **Middleware** (outer / inner, instance-based): `outer_middleware(mw)` / `inner_middleware(mw)`
  на `MaxBot` или `Router`. Middleware — callable-объект или функция, не декоратор.
  Порядок: `app.outer → router.outer → app.inner → router.inner → handler`.
- **FSM** (`src/maxio/fsm/`): `StatesGroup`, `State`, `FSMContext`, `StateFilter`, `MemoryStorage`.
  `FSMContext` инжектируется в хэндлер по аннотации типа; `StateFilter` — обычный фильтр.
  По умолчанию используется `MemoryStorage`; хранилище подключается через `MaxBot(storage=...)`.
- **Медиа**: `Bot.upload(file, UploadType.IMAGE | VIDEO | AUDIO | FILE)` → токен.
  Фабрики `media.image/video/audio/file(token)` для параметра `attachments`.
  `Message.photos`, `.videos`, `.audio`, `.files` — типизированные payload-объекты входящих вложений.
  `HasMedia(*types)` — фильтр по типу вложения.

## [0.2.0] — 2026-05-27

### Безопасность
- Токен больше не утекает в логи: при `logging.INFO` httpx писал полный URL с
  query-параметром `access_token`. Добавлен фильтр `TokenMaskingFilter`, который маскирует
  `access_token=...` и `Authorization: ...` на `***`.
- У `Bot` появился параметр `mask_token_in_logs: bool = True` (включён по умолчанию).

### Изменено (breaking)
- Декоратор `MaxBot.startup()` переименован в `bot_started()` — имя совпадает с типом
  события MAX.
- Типы `Callback` и `CallbackQuery` объединены в один `Callback`.

### Добавлено
- `callback.message.answer()` / `.reply()` — отправка из обработчика нажатия кнопки.

## [0.1.0] — 2025-05-27

### Added
- Long polling с автоматическим переподключением
- HTTP-клиент: `get_me`, `send_message`, `edit_message`, `delete_message`, `get_messages`, `get_chats`, `answer_callback`, `get_updates`
- Декораторы событий: `message`, `message_edited`, `callback`, `startup`, `event`
- Внедрение зависимостей по аннотациям типов (без `Depends()`)
- Фильтры: `Command`, `CallbackPayload`, произвольный `Callable`
- Inline-клавиатуры: `InlineKeyboard` + `Button.callback` / `Button.link` / `Button.request_geo_location`
- Сахар на моделях: `Message.answer()`, `Message.reply()`, `CallbackQuery.answer()`
- Pydantic v2, `py.typed`, совместимость с `mypy --strict`

[Unreleased]: https://github.com/rlxrd/maxio/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/rlxrd/maxio/compare/v0.4...v0.5.0
[0.4.0]: https://github.com/rlxrd/maxio/compare/v0.3.0...v0.4
[0.3.0]: https://github.com/rlxrd/maxio/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/rlxrd/maxio/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rlxrd/maxio/releases/tag/v0.1.0
