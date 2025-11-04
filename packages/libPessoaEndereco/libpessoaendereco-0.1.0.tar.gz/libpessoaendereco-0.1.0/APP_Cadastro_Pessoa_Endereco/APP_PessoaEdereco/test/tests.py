import pytest
from model.models import Pessoa, Endereco

def test_create_pessoa():
    """
    Teste de criar pessoa:
    """
    pessoa = Pessoa(nome="Lucas Mariani", idade="21", email="lucas2607.gomes@gmail.com")
    assert pessoa.nome == "Lucas Mariani"
    assert pessoa.idade == "21"
    assert pessoa.email == "lucas2607.gomes@gmail.com"

def test_create_endereco():
    """
    Teste de criar endereco:
    """

    endereco = Endereco(logradouro="Carvalho", numero="01", cidade="Vitoria")
    assert endereco.logradouro == "Carvalho"
    assert endereco.numero == "01"
    assert endereco.cidade == "Vitoria"