from setuptools import setup, find_packages

setup(
    name="cli-botx",
    version="1.0.0",
    author="Yatin Annam",
    description="A simple command-line assistant with calculator, web shortcuts, and task list.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yatinannam/cli-bot",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "cli-botx=cli_bot.bot:main",
        ],
    },
)
