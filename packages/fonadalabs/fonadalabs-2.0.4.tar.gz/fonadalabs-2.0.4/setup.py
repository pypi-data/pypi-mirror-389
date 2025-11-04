"""
FonadaLabs SDK - Unified package for TTS, ASR, and Audio Denoising
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fonadalabs",
    version="2.0.4",
    author="FonadaLabs",
    author_email="support@fonadalabs.com",
    description="Unified Python SDK for FonadaLabs Text-to-Speech, Automatic Speech Recognition, and Audio Denoising APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fonadalabs/fonadalabs-sdk",
    packages=find_packages(exclude=["tests", "examples", "tts_sdk", "asr_sdk", "denoise_sdk"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24,<1.0",
        "websockets>=11,<13",
        "loguru>=0.7,<1.0",
        "requests>=2.28,<3.0",
        "numpy>=1.21,<2.0",
    ],
    extras_require={
        "ws": [
            "soundfile>=0.12,<0.14",
            "websocket-client>=1.5,<2.0",
        ],
        "denoise": [
            "soundfile>=0.12,<0.14",
            "librosa>=0.10,<1.0",
            "websocket-client>=1.5,<2.0",
        ],
        "dev": [
            "pytest>=7.0,<8.0",
            "black>=23.0,<24.0",
            "isort>=5.0,<6.0",
            "python-dotenv>=1.0,<2.0",
            "nest-asyncio>=1.5,<2.0",  # For testing in Jupyter/IPython environments
        ],
        "all": [
            "soundfile>=0.12,<0.14",
            "librosa>=0.10,<1.0",
            "websocket-client>=1.5,<2.0",
        ],
    },
    include_package_data=True,
)


