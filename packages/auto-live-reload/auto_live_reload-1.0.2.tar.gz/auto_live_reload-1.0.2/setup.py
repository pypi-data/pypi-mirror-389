from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    long_description=long_description,
    long_description_content_type="text/markdown",
    name='auto-live-reload',
    version='1.0.2',
    packages=['auto_live_reload'],
    description='A Python library for live reloading scripts on file changes.',
    author="CrypterENC",
    author_email="a95899003@gmail.com",
    url='https://github.com/CrypterENC/auto-live-reload.git',
    python_requires=">=3.8",
    license="MIT",
)
