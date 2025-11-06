# persian_tts/utils.py
import os
import aiohttp
import asyncio

AUDIO_DIR = os.path.join(os.getcwd(), "tts_output")
os.makedirs(AUDIO_DIR, exist_ok=True)

async def save_audio_from_url(audio_url: str, filename: str) -> str:
    """دانلود و ذخیره فایل صوتی به صورت async"""
    file_path = os.path.join(AUDIO_DIR, filename)
    async with aiohttp.ClientSession() as session:
        async with session.get(audio_url) as resp:
            if resp.status != 200:
                raise Exception(f"خطا در دریافت صدا: {resp.status}")
            with open(file_path, "wb") as f:
                while True:
                    chunk = await resp.content.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
    return file_path
