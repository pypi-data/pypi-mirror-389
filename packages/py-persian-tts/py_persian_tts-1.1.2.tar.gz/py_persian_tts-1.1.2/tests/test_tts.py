from py_persian_tts import PersianTTS, list_voices


tts = PersianTTS(default_voice="man1")

# نمایش شخصیت‌ها
print("شخصیت‌ها:", list_voices())

# تبدیل متن به صدا و ذخیره با نام دلخواه
file_path = tts.speak(
    "سلام! این یک تست پیشرفته کتابخانه TTS است.",
    voice="woman2",
    filename="test.wav"
)

print("فایل صوتی ذخیره شد:", file_path)
