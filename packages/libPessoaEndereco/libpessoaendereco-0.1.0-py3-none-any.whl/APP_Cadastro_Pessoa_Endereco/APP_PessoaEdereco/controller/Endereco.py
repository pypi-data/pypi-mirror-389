# app/routers/endereco.py
from fastapi import HTTPException
from sqlmodel import Session, select
from controller.generic import create_crud_router, Hooks
from model.models import Endereco, Pessoa
from model.dto import EnderecoCreate, EnderecoUpdate, EnderecoRead

class EnderecoHooks(Hooks[Endereco, EnderecoCreate, EnderecoUpdate]):
    def pre_create(self, payload: EnderecoCreate, session: Session) -> None:
        # se for criar vinculado a uma Pessoa, valida
        if payload.pessoa_id is None or payload.pessoa_id <= 0 or not session.get(Pessoa, payload.pessoa_id):
            raise HTTPException(400, "pessoa_id inválido")


router = create_crud_router(
    model=Endereco,
    create_schema=EnderecoCreate,
    update_schema=EnderecoUpdate,
    read_schema=EnderecoRead,
    prefix="/enderecos",
    tags=["enderecos"],
    hooks=EnderecoHooks(),
)
