from setuptools import setup, find_packages
import pathlib

# خواندن توضیحات از README.md
current_dir = pathlib.Path(__file__).parent
long_description = (current_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="py_persian_tts",
    version="1.2.2",
    author="AmirhosseinPython",
    author_email="amirhossinpython03@gmail.com",
    description="کتابخانه تبدیل متن به گفتار فارسی با پشتیبانی از چندین شخصیت صوتی",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amirhossinpython/py_persian_tts",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.0",  # اصلاح شده: حذف > اضافی
        "gtts>=2.3.0"
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: Persian",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    keywords="persian tts text-to-speech farsi",
    entry_points={
        'console_scripts': [
            'persian-tts=py_persian_tts.cli:main',
        ],
    },
)