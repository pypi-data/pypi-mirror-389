# app/models.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# ---------- PESSOA ----------
class PessoaBase(SQLModel):
    name: str = Field(min_length=2, max_length=120)
    idade: int = Field(ge=0, le=200)
    email: str = Field(min_length=10, max_length=200)

class Pessoa(PessoaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # back_populates liga Pessoa <-> Endereco
    enderecos: List["Endereco"] = Relationship(back_populates="pessoa")


# ---------- ENDEREÇO ----------
class EnderecoBase(SQLModel):
    logradouro: str = Field(min_length=2, max_length=200)
    numero: str = Field(min_length=1, max_length=20)
    cidade: str = Field(min_length=2, max_length=100)
    bairro: str = Field(min_length=2, max_length=100)
    estado: str = Field(min_length=2, max_length=100)

class Endereco(EnderecoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    pessoa_id: int = Field(default=None, foreign_key="pessoa.id")
    pessoa : Optional["Pessoa"] = Relationship(back_populates="enderecos")
