from sqlmodel import SQLModel, Session, create_engine
from typing import Annotated
from fastapi import Depends
import os

# Definindo a url do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Args para a conexão
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Criando a engine para o controle do pool de conexões com o banco de dados
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

# Inicialização do banco
def init_db() -> None:
    SQLModel.metadata.create_all(engine)
# fim_init_db

# Gerador de sessões com o banco (e encerramento)
def get_session():
    with Session(engine) as session:
        yield session
    # fim_with
# fim_get_session

# Aplicando a injeção de dependência para todos os usos de SessionDep
SessionDep = Annotated[Session, Depends(get_session)]
