from setuptools import setup, find_packages

# Lendo o README.md para o PyPI
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cadastroPessoaEndereco-Lib",  # ⚡ Nome com hífen para o PyPI
    version="0.1.0",
    description="Biblioteca que permite o cadastro de pessoas e endereços e gera um banco de dados.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lucas Mariani Gomes",
    author_email="lucas2607.gomes@gmail.com",
    url="https://github.com/LucasMarianiG/PessoaEndereco-lib.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)