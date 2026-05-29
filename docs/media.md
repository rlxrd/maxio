# Медиа

## Отправка файлов

Загрузка — двухшаговый процесс: сначала загрузить файл, получить токен, затем отправить с токеном.

```python
from maxio import media
from maxio.enums import UploadType
from pathlib import Path

@app.message(Command("photo"))
async def send_photo(message: Message, bot: Bot) -> None:
    token = await bot.upload(Path("photo.jpg"), UploadType.IMAGE)
    await message.answer("Держи!", attachments=[media.image(token)])
```

### Типы загрузки

| `UploadType` | Фабрика | Расширения |
|---|---|---|
| `IMAGE` | `media.image(token)` | jpg, png, gif, webp… |
| `VIDEO` | `media.video(token)` | mp4, mov… |
| `AUDIO` | `media.audio(token)` | mp3, ogg, m4a… |
| `FILE` | `media.file(token)` | любые |

### Источник файла

`bot.upload` принимает `Path`, `bytes` или `IO[bytes]`:

```python
# Из файла
token = await bot.upload(Path("photo.jpg"), UploadType.IMAGE)

# Из байт
data = open("photo.jpg", "rb").read()
token = await bot.upload(data, UploadType.IMAGE)
```

---

## Приём медиа

### F-фильтры

```python
@app.message(F.photo)
async def got_photo(message: Message) -> None:
    for photo in message.photos:
        await message.answer(f"Фото: {photo.url}")

@app.message(F.video)
async def got_video(message: Message) -> None:
    await message.answer(f"Видео: {len(message.videos)} шт.")

@app.message(F.file)
async def got_file(message: Message) -> None:
    for f in message.files:
        await message.answer(f"{f.filename} — {f.size} байт")

@app.message(F.audio)
async def got_audio(message: Message) -> None:
    await message.answer("Аудио получено!")
```

### HasMedia

```python
from maxio import HasMedia

@app.message(HasMedia("image"))   # только фото
async def got_photo(message: Message) -> None: ...

@app.message(HasMedia())          # любое вложение
async def got_any(message: Message) -> None:
    types = {a.type for a in message.attachments}
    await message.answer(f"Вложения: {', '.join(sorted(types))}")
```

### Поля Message

```python
message.photos    # list[PhotoAttachmentPayload]
message.videos    # list[VideoAttachmentPayload]
message.audios    # list[AudioAttachmentPayload]
message.files     # list[FileAttachmentPayload]
message.attachments  # list[Attachment] — все вложения
```
