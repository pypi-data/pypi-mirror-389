from setuptools import setup, find_packages

setup(
    name="eldar-emoji-art",
    version="1.0.0",
    author="Eldar Eliyev",
    author_email="example@email.com",
    description="Emoji-lərlə mətn bəzək kitabxanası 💫🔥",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
)
