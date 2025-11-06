from pathlib import Path
from setuptools import setup, find_packages

readme = Path(__file__).with_name("README.md")
long_description = readme.read_text(encoding="utf-8") if readme.exists() else "AutoWebX toolkit"

setup(
    name='autowebx',
    version='1.11',
    description='Automation helpers: temp email, captcha solvers, proxies, Playwright humanizer, and more',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.9',
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'functioner = autowebx.__init__:__get_function__',
            'shuffle = autowebx.__init__:__shuffle',
        ],
    },

    install_requires=[
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.2',
        'names>=0.3.0',
        'phonenumbers>=8.13.0',
        'colorama>=0.4.6',
        'art>=6.5',
        'multipledispatch>=1.0.0',
        'ntplib>=0.4.0',
    ]
)
