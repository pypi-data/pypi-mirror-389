from setuptools import setup, find_packages

setup(
    name="aiomrim",
    version="1.1",
    packages=find_packages(),
    install_requires=[
        "aiohttp >= 3.12.0",
        "asyncio >= 3.4.3",
    ],
    entry_points={
        'console_scripts': [
            'aiomrim=aiomrim:hello',
        ],
    },
    author="fayzetwin",
    author_email="contact@fayzetwin.xyz",
    description="Awesome SDK for Async Operations with MRIM-Server (https://github.com/mrimsu/mrim-server)",
    url="https://github.com/fayzetwin1/aiomrim")