# ps_pessoa_fastapi_lib

Lib de Cadastro de Pessoas e Endereços desenvolvida com SQLModel.
Aplicação de Cadastro de Pessoas e Endereços desenvolvida com FastAPI e a lib implementada.

## Visão Geral

Este projeto simula o funcionamento de um banco de pessoas, permitindo o cadastro e gerenciamento de pessoas e endereços. Utiliza FastAPI para a API REST e SQLModel para o mapeamento dos modelos e persistência em banco de dados.

## Funcionalidades

- Cadastro de pessoas
- Cadastro de endereços
- Validações automáticas via FastAPI

## Requisitos

- [Python 3.11+](https://www.python.org/about/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)

## Ambiente do projeto

### Baixando o código

```bash
git clone https://github.com/douglasbolis/ps_pessoa_fastapi_lib.git
cd ps_pessoa_fastapi_lib
```

### Ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Instalação dos pacotes

```bash
pip install -r requirements.txt
```

Pode ser que dê problema, então instale os pacotes separadamente.

```bash
pip install sqlmodel "fastapi[standard]" ps_pessoas_fastapi_lib
```

## Publicação da LIB
---

## Execução

```bash
fastapi dev app/main.py # Linux/Mac
fastapi dev .\app\main.py # Windows
```

Acesse a documentação interativa em [http://localhost:8000/docs](http://localhost:8000/docs).

## Estrutura do Projeto

```
.
├── LICENSE                    # Licença do projeto
├── README.md                  # Documentação do projeto
├── app
│   ├── controller             # Rotas e lógica de negócio
│   │   ├── endereco.py
│   │   ├── generic.py
│   │   └── pessoa.py
│   ├── main.py                # Inicialização da aplicação FastAPI
│   ├── model                  # Modelos e DTOs
│   │   ├── dto.py
│   │   └── models.py
│   ├── repository             # Repositórios de acesso a dados
│   │   └── base.py
│   ├── service                # Serviços de negócio
│   │   └── base.py
│   └── util                   # Utilitários e configuração do banco
│       └── database.py
├── app.db                     # Banco de dados em memória
└── requirements.txt           # Pacotes (dependências) para instalação
```

## Licença

Este projeto está sob a licença MIT.
