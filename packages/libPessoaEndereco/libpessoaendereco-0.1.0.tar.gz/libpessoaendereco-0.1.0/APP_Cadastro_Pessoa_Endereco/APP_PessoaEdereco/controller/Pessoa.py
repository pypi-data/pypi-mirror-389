# app/routers/pessoa.py
from controller.generic import create_crud_router
from model.models import Pessoa 
from model.dto import PessoaCreate, PessoaUpdate, PessoaRead

router = create_crud_router(
    model=Pessoa,
    create_schema=PessoaCreate,
    update_schema=PessoaUpdate,
    read_schema=PessoaRead,
    prefix="/pessoas",
    tags=["pessoas"],
)
