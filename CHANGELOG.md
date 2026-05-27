# Changelog

## [Unreleased]

## [0.2.0] — 2026-05-27

### Безопасность
- Токен больше не утекает в логи: при `logging.INFO` httpx писал полный URL с
  query-параметром `access_token`. Добавлен фильтр `TokenMaskingFilter`, который маскирует
  `access_token=...` и `Authorization: ...` на `***`.
- У `Bot` появился параметр `mask_token_in_logs: bool = True` (включён по умолчанию),
  прокидывается и через `MaxBot(token, ...)`.

### Изменено (breaking)
- Декоратор `MaxBot.startup()` переименован в `bot_started()` — имя совпадает с типом
  события MAX. Синяя кнопка Start шлёт событие `bot_started` (без `message`), а не команду
  `/start`, поэтому ловить её нужно через `@app.bot_started()`.
- Типы `Callback` и `CallbackQuery` объединены в один `Callback` (поля `message`, `user`,
  `from_user`, метод `answer()`). `CallbackQuery` удалён.
- В хэндлерах рекомендуемое имя аргумента — `callback: Callback` (по аналогии с `message: Message`).

### Добавлено
- `callback.message.answer()` / `.reply()` — отправка сообщения в чат из обработчика
  нажатия кнопки (исходное сообщение проставляется в `callback.message`).

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

[Unreleased]: https://github.com/rlxrd/maxio/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/rlxrd/maxio/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rlxrd/maxio/releases/tag/v0.1.0
