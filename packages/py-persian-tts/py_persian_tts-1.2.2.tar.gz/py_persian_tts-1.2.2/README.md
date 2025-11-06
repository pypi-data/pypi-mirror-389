# PersianTTS

یک کتابخانه فارسی برای تبدیل متن به صدا با شخصیت‌های مختلف.

این کتابخانه به شما امکان می‌دهد متن فارسی را با صدای شخصیت‌های متفاوت به فایل صوتی تبدیل کنید و آن را ذخیره نمایید.

---

## نصب

برای نصب کتابخانه، ابتدا اطمینان حاصل کنید که Python 3.8 یا بالاتر دارید و سپس از pip استفاده کنید:


---
## لیست شخصیت‌ها (Voices)
| کلید شخصیت | نام شخصیت |
| ---------- | --------- |
| woman1     | 🌼 شیوا   |
| woman2     | 🌷 مهتاب  |
| woman3     | 🌺 نگار   |
| woman4     | 🌹 ریما   |
| man1       | 🌠 راد    |
| man2       | 🌠 پیام   |
| man3       | 🚀 بهمن   |
| man4       | 🚀 برنا   |
| man5       | 🚀 برنا-1 |
| man6       | 🦁 کیان   |
| man7       | 💧 نیما   |
| man8       | ⚡️ آریا   |
| boy1       | 🌟 آرش    |



```python
from py_persian_tts import PersianTTS, list_voices
import asyncio

async def main():
    tts = PersianTTS(default_voice="man1")
    
    # نمایش شخصیت‌ها
    print("شخصیت‌ها:", list_voices())
    
    # تبدیل متن به صدا (نسخه async)
    await tts.speak_async("سلام این یک تست است.", voice="man2", filename="tewst.wav")
    print("عملیات با موفقیت انجام شد")



# اجرای تابع async
if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from py_persian_tts import PersianTTS

async def main():
    tts = PersianTTS(default_voice="man1", rate_limit=0.5)  # هر 2 ثانیه یک درخواست

    texts = [
        "سلام این یک تست است",
        "این هم متن دوم برای تست صف TTS.",
        
    ]

    tasks = []
    for i, text in enumerate(texts):
        filename = f"tts_queue_{i+1}.wav"
        # اضافه کردن هر متن به صف و گرفتن Future
        tasks.append(tts.speak_async(text, filename=filename))

    # اجرای همه و گرفتن مسیر فایل‌ها
    results = await asyncio.gather(*tasks)
    for path in results:
        print("فایل صوتی ذخیره شد:", path)

    # پایان کار و توقف پردازش صف
    await tts.shutdown()

# اجرای مثال
asyncio.run(main())


```bash
pip install --upgrade  py-persian-tts 