import aiohttp
import time
from .voices import VOICES
from .utils import save_audio_from_url
import asyncio

class PersianTTS:
    def __init__(self, default_voice="woman1", rate_limit: float = 0.5):
        """
        :param default_voice: صدای پیش‌فرض
        :param rate_limit: نرخ درخواست (چند درخواست در ثانیه مجاز است).
    مثلا 0.5 یعنی هر 2 ثانیه یک درخواست (پیش‌فرض).
        """
        if default_voice not in VOICES:
            raise ValueError("صدای پیش‌فرض نامعتبر است.")
        self.default_voice = default_voice
        self.rate_limit = rate_limit
        self._last_request_time = 0
        self._queue = asyncio.Queue()  # صف درخواست‌ها
        self._queue_worker_task = None

    def list_voices(self):
        """بازگرداندن لیست شخصیت‌ها"""
        return list(VOICES.keys())

    async def _respect_rate_limit(self):
        """رعایت محدودیت نرخ درخواست‌ها"""
        elapsed = time.time() - self._last_request_time
        min_interval = 1 / self.rate_limit if self.rate_limit > 0 else 0
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

    async def _process_queue(self):
        """پردازش صف به ترتیب"""
        while True:
            item = await self._queue.get()
            if item is None:
                break  # سیگنال توقف
            text, voice, filename, retries, future = item
            try:
                result = await self._speak_internal(text, voice, filename, retries)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            self._queue.task_done()

    async def _speak_internal(self, text: str, voice: str, filename: str, retries: int):
        """متد داخلی پردازش TTS"""
        voice_name = VOICES[voice] if voice else VOICES[self.default_voice]
        api_url = "https://karim23657-persian-tts-sherpa.hf.space/submit"

        for attempt in range(retries):
            await self._respect_rate_limit()
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, data={"tab": "tts", "text": text, "voice": voice_name}) as resp:
                    if resp.status == 429:
                        wait_time = 2 ** attempt  # exponential backoff
                        print(f"⚠️ محدودیت درخواست! تلاش دوباره در {wait_time} ثانیه...")
                        await asyncio.sleep(wait_time)
                        continue
                    elif resp.status != 200:
                        raise Exception(f"خطا در ارسال درخواست: {resp.status}")
                    result = await resp.json()

            self._last_request_time = time.time()
            task_id = result.get("task_id")
            if not task_id:
                raise Exception("دریافت task_id با شکست مواجه شد")

            result_url = f"https://karim23657-persian-tts-sherpa.hf.space/result/{task_id}/tts"

            for _ in range(20):
                await asyncio.sleep(2)
                async with aiohttp.ClientSession() as session:
                    async with session.get(result_url) as resp:
                        if resp.status != 200:
                            continue
                        res = await resp.json()
                        status = res.get("status", "")
                        if status in ["success", "completed"]:
                            audio_path = res.get("result", {}).get("audio")
                            if not audio_path:
                                break
                            full_audio_url = f"https://karim23657-persian-tts-sherpa.hf.space{audio_path}"
                            filename = filename or f"tts_{int(time.time())}.wav"
                            return await save_audio_from_url(full_audio_url, filename)
                        elif status == "error":
                            raise Exception("خطا در پردازش TTS")

            raise TimeoutError("پردازش طولانی شد، دوباره تلاش کنید")

        raise Exception("تمام تلاش‌ها برای تولید صدا شکست خورد.")

    async def speak_async(self, text: str, voice: str = None, filename: str = None, retries: int = 3):
        """اضافه کردن درخواست به صف و بازگرداندن نتیجه"""
        if self._queue_worker_task is None:
            self._queue_worker_task = asyncio.create_task(self._process_queue())

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self._queue.put((text, voice, filename, retries, future))
        return await future

    def speak(self, *args, **kwargs):
        """متد sync برای استفاده ساده"""
        return asyncio.run(self.speak_async(*args, **kwargs))

    async def shutdown(self):
        """توقف صف و پاکسازی"""
        if self._queue_worker_task:
            await self._queue.put(None)  # سیگنال توقف
            await self._queue_worker_task
            self._queue_worker_task = None
