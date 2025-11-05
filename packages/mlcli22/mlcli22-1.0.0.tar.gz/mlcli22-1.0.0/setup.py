from setuptools import setup

setup(
    name="mlcli22",
    version="1.0.0",
    py_modules=["mlcli22"],
    install_requires=[
        "typer",
        "PyYAML"
    ],
    entry_points={
        "console_scripts": [
            "mlcli22=mlcli22:app",  # Comando que se ejecutará en la terminal
        ],
    },
    author="Yilber Sisco",
    description="CLI para gestionar proyectos de Machine Learning",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ysisco/mlcli22",  # Repositorio opcional
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)