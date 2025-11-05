from setuptools import setup
from pathlib import Path

here = Path(__file__).parent
readme = (here / "README.md").read_text(encoding="utf-8") if (here / "README.md").exists() else ""

setup(
    name="rubika-bot-api",
    version="1.1.0",
    description="A powerful asynchronous/synchronous library for Rubika Bot API with a focus on high performance.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="rubika api bot",
    author_email="0x01101101@proton.me",
    url="https://github.com/rubika-bot-api/rubika_bot_api",
    license="MIT",
    packages=["rubika_bot_api"],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp",
        "aiofiles",
        "requests",
        "pytz",
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
