from typing import Optional, List
from datetime import datetime
from sqlmodel import Field
from model.models import PessoaBase, EnderecoBase

# ====================================================================
#                           ENDERECO
# ====================================================================

class EnderecoCreate(EnderecoBase):
    pessoa_id: int
# fim_class

class EnderecoUpdate(EnderecoBase):
    logradouro: Optional[str] = Field(default=None, max_length=255)
    bairro: Optional[str] = Field(default=None, max_length=100)
    cidade: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[str] = Field(default=None, max_length=2)
# fim_class

class EnderecoReadBase(EnderecoBase):
    id: int
    pessoa_id: int
# fim_class

class EnderecoRead(EnderecoReadBase):
    pessoa: Optional["PessoaReadBase"] = None
    model_config = {"from_attributes": True}
# fim_class

# ====================================================================
#                          PESSOA
# ====================================================================

class PessoaCreate(PessoaBase):
    pass
# fim_class

class PessoaUpdate(PessoaBase):
    nome: Optional[str] = Field(default=None, min_length=2, max_length=120)
    idade: Optional[int] = Field(default=None, ge=0, le=200)
    email: Optional[str] = Field(default=None, min_length=10, max_length=100)
# fim_class

class PessoaReadBase(PessoaBase):
    id: int
# fim_class

class PessoaRead(PessoaBase):
    id: int
    enderecos: List[EnderecoReadBase] = []
    model_config = {"from_attributes": True}
# fim_class
