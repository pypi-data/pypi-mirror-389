from model.models import Endereco, EnderecoBase, Pessoa, PessoaBase
from typing import  List, Optional
from sqlmodel import Field



class PessoaCreate(PessoaBase):
    pass


class PessoaPublic(PessoaBase):
    id: int
    model_config = {"from_attributes": True}


class PessoaWithEndereco(PessoaPublic):
    enderecos: List["EnderecoPublic"] = []
    model_config = {"from_attributes": True}    


class PessoaRead(PessoaWithEndereco):
    id: int
    

class PessoaUpdate(PessoaBase):
    nome: Optional[str] = None
    idade: Optional[int] = None
    email: Optional[str] = None


class EnderecoCreate(EnderecoBase):
    pessoa_id: int   # permite já criar vinculado a uma Pessoa
    

class EnderecoUpdate(EnderecoBase):
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    cidade: Optional[str] = None
    bairro: Optional[str] = None
    estado: Optional[str] = None
    

class EnderecoPublic(EnderecoBase):
    id: int
    model_config = {"from_attributes": True}


class EnderecoRead(EnderecoPublic):
    id: int
    pessoa_id: int
