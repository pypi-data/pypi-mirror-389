from setuptools import setup, find_packages

setup(
    name="Anshul",
    version="1.0.1",
    author="Anshul Dubey",
    author_email="anshul@example.com",
    description="A YouTube & Spotify downloader with auto-setup and updates.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'anshul=Anshul.main:main',
        ],
    },
    install_requires=['yt-dlp','spotdl'],
    python_requires=">=3.6",
)