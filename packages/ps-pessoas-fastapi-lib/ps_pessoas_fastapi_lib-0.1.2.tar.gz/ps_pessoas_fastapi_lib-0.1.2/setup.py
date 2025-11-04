from setuptools import setup, find_packages

# Lendo o README.md para o PyPI
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ps-pessoas-fastapi-lib",
    version="0.1.2",
    description="Biblioteca do model de Pessoa e Endereço com banco de dados.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Douglas Lima",
    author_email="douglasbolislima@gmail.com",
    url="https://github.com/douglasbolis/ps_pessoa_fastapi_lib",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
