# Changelog

## [Unreleased]

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

[Unreleased]: https://github.com/yourusername/maxio/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/maxio/releases/tag/v0.1.0
