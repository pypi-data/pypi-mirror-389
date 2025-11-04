from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


# ====================================================================
#                            ENDERECO
# ====================================================================

class EnderecoBase(SQLModel):
    logradouro: str = Field(max_length=255)
    numero: Optional[str] = Field(default=None, max_length=10)
    cep: Optional[str] = Field(default=None, min_length=8, max_length=8)
    bairro: str = Field(max_length=100)
    cidade: str = Field(max_length=100)
    estado: str = Field(max_length=2)
    complemento: Optional[str] = Field(default=None, max_length=255)
# fim_class

class Endereco(EnderecoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Relacionamento com Pessoa
    pessoa_id: int = Field(foreign_key="pessoa.id")
    pessoa: "Pessoa" = Relationship(back_populates="enderecos")
# fim_class

# ====================================================================
#                              PESSOA
# ====================================================================

class PessoaBase(SQLModel):
    nome: str = Field(min_length=2, max_length=120)
    idade: int = Field(ge=0, le=200)
    email: str = Field(min_length=10, max_length=100)
    telefone: Optional[str] = Field(default=None, max_length=20)
# fim_class

class Pessoa(PessoaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    # Relacionamento 1-N com Endereço
    enderecos: List[Endereco] = Relationship(back_populates="pessoa")
# fim_class
