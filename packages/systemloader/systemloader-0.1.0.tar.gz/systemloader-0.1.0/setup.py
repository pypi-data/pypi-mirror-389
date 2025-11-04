from setuptools import setup, find_packages

setup(
    name="systemloader",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",  # для CLI
        "Jinja2>=3.0.0", # для шаблонов
    ],
    entry_points={
        "console_scripts": [
            "systemloader=systemloader.cli:main",  # точка входа для команды
        ],
    },
    author="Your Name",
    author_email="videoproc@yandex.ru",
    description="Загрузка движка",
    keywords="cli, project templates",
    python_requires=">=3.12",
)
