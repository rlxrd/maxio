"""
media_upload_bot.py — загрузка и обработка медиа.

Показывает: Bot.upload, media.image/video/file, get_video_info,
            F.photo/F.video/F.file.

Запуск:
    MAX_TOKEN=<токен> python examples/media_upload_bot.py
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from maxio import Bot, Command, F, MaxBot, Message, UploadType, media

logging.basicConfig(level=logging.INFO)

app = MaxBot(os.environ["MAX_TOKEN"])

SAMPLE_IMAGE = Path(__file__).with_name("sample.jpg")
SAMPLE_VIDEO = Path(__file__).with_name("sample.mp4")
SAMPLE_FILE = Path(__file__).with_name("sample.txt")


@app.message(Command("photo"))
async def cmd_photo(message: Message, bot: Bot) -> None:
    if not SAMPLE_IMAGE.exists():
        await message.answer("Положи файл examples/sample.jpg и повтори /photo.")
        return

    token = await bot.upload(SAMPLE_IMAGE, UploadType.IMAGE)
    await message.answer("Фото загружено.", attachments=[media.image(token)])


@app.message(Command("video"))
async def cmd_video(message: Message, bot: Bot) -> None:
    if not SAMPLE_VIDEO.exists():
        await message.answer("Положи файл examples/sample.mp4 и повтори /video.")
        return

    token = await bot.upload(SAMPLE_VIDEO, UploadType.VIDEO)
    info = await bot.get_video_info(token)
    details = f"{info.width or '?'}x{info.height or '?'}" if info.width or info.height else "?"
    await message.answer(
        f"Видео загружено: {details}, длительность: {info.duration or '?'} сек.",
        attachments=[media.video(token)],
    )


@app.message(Command("file"))
async def cmd_file(message: Message, bot: Bot) -> None:
    if not SAMPLE_FILE.exists():
        await message.answer("Положи файл examples/sample.txt и повтори /file.")
        return

    token = await bot.upload(SAMPLE_FILE, UploadType.FILE)
    await message.answer("Файл загружен.", attachments=[media.file(token)])


@app.message(F.photo)
async def got_photo(message: Message) -> None:
    urls = [photo.url for photo in message.photos if photo.url]
    await message.answer("Получил фото:\n" + "\n".join(urls or ["URL недоступен"]))


@app.message(F.video)
async def got_video(message: Message) -> None:
    await message.answer(f"Получил видео: {len(message.videos)} шт.")


@app.message(F.file)
async def got_file(message: Message) -> None:
    lines = [f"{item.filename or 'file'} ({item.size or '?'} байт)" for item in message.files]
    await message.answer("Получил файл:\n" + "\n".join(lines))


if __name__ == "__main__":
    app.run()
