# Sistema Integrado de Atendimento e Execução de Serviços - Oficina Mecânica

> **Tech Challenge — Fase 1 | Pós-Graduação em Arquitetura de Software (SOAT FIAP)**

## 1. Objetivo do Projeto
Desenvolvimento da primeira versão (MVP) do back-end de um sistema integrado para gestão de oficinas mecânicas de médio porte. O sistema resolve gargalos operacionais como anotações manuais, falhas no controle de estoque de peças, perda de histórico de clientes e desorganização no fluxo de orçamentos e ordens de serviço (OS).

## 2. Descrição Resumida da Solução
Back-end monolítico em camadas desenvolvido em **Python (FastAPI)**, aplicando princípios de **Domain-Driven Design (DDD)**. O sistema gerencia o ciclo de vida completo de Ordens de Serviço (com máquina de estados rígida), controle transacional de estoque de peças e insumos, autenticação **JWT** para rotas administrativas, e um portal de API pública para que clientes consultem o progresso e aprovem ou rejeitem orçamentos em tempo real.

## 3. Arquitetura Utilizada
- **Arquitetura em Camadas + Domain-Driven Design (DDD):**
  - `app/domain`: Entidades de Domínio, Objetos de Valor (CPF/CNPJ e Placa validados algoritmicamente), Regras de Negócio e Interfaces (Portas).
  - `app/application`: Casos de Uso (`Use Cases`), orquestração de transações e cálculo de métricas de tempo médio.
  - `app/infrastructure`: Persistência com SQLAlchemy 2.0, Modelos ORM, Repositórios Concretos e Gerenciador JWT (`bcrypt`).
  - `app/presentation`: Endpoints RESTful (FastAPI), Schemas de validação Pydantic e Injeção de Dependências.

## 4. Tecnologias Utilizadas
- **Linguagem:** Python 3.12+ / 3.14
- **Framework Web:** FastAPI (com geração nativa OpenAPI/Swagger)
- **ORM:** SQLAlchemy 2.0
- **Banco de Dados:** SQLite (desenvolvimento/testes locais) & PostgreSQL 16 (produção via Docker)
- **Autenticação:** PyJWT (HS256) + Passlib/Bcrypt
- **Testes & Qualidade:** Pytest, Pytest-Cov (Cobertura > 90%) e Bandit (Análise de Segurança)
- **Containerização:** Docker & Docker Compose

## 5. Pré-requisitos
- Python 3.12 ou superior instalado.
- Docker e Docker Compose (caso deseje rodar com PostgreSQL).

## 6. Instruções para Execução Local (Python nativo)
1. Clone o repositório e acesse a pasta raiz:
  ```powershell```
git clone [https://github.com/leoffleoff/tech-challenge-oficina-mecanica-soat.git](https://github.com/leoffleoff/tech-challenge-oficina-mecanica-soat.git)
cd tech-challenge-oficina-mecanica

2. Crie e ative o ambiente virtual:
  ```powershell```
python -m venv venv
.\venv\Scripts\Activate.ps1

3. Instale as dependências:
  ```powershell```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

4. Copie o arquivo de exemplo de ambiente e inicie a API:
  ```powershell```
Copy-Item .env.example .env
uvicorn app.main:app --reload

## 7. Instruções para Execução via Docker (Ambiente Completo com PostgreSQL)
Se preferir rodar a aplicação containerizada com o banco de dados PostgreSQL integrado:
  ```powershell```
docker-compose up --build

## 8. Instruções para Execução dos Testes
Para rodar toda a suíte de testes unitários e de integração com relatório de cobertura:
  ```powershell```
pytest tests/ -v --cov=app --cov-report=term-missing

## 9. Instruções para Acesso ao Swagger
Com a aplicação rodando, acesse no navegador:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## 10. Decisão e Justificativa do Banco de Dados Escolhido
SQLite: Utilizado em ambiente de desenvolvimento local e suíte de testes automatizados por sua simplicidade, ausência de dependências externas e velocidade na execução em memória.

PostgreSQL: Escolhido como banco padrão para o ambiente containerizado de produção (Docker Compose). A justificativa técnica principal baseia-se na garantia de atomicidade e consistência ACID rigorosa, indispensáveis para evitar concorrência e inconsistências críticas no controle de estoque de peças e nas transações financeiras de orçamentos e ordens de serviço.

## 11. Usuários e Credenciais de Demonstração (Seed Inicial)
O sistema cria automaticamente um usuário administrador padrão ao inicializar:

Username: admin

Password: AdminPassword@2026

Para acessar as rotas administrativas no Swagger, clique em Authorize no canto superior direito e faça login.

## 12. Estrutura dos Principais Diretórios do Projeto
Plaintext
tech-challenge-oficina-mecanica/
├── app/
│   ├── application/     # Casos de uso e lógica de aplicação
│   ├── domain/          # Entidades, VOs, Exceções e Regras de Negócio (DDD)
│   ├── infrastructure/  # Repositórios SQLAlchemy, Modelos e JWT
│   └── presentation/    # Endpoints REST (FastAPI) e Schemas Pydantic
├── tests/
│   ├── integration/     # Testes E2E de API e banco de dados
│   └── unit/            # Testes unitários de domínio e infraestrutura
├── docs/
│   ├── ddd/             # Diagramas, Event Storming e Linguagem Ubíqua
│   └── security/        # Relatório de vulnerabilidades Bandit
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

## 13. Link para a Documentação DDD
A documentação completa contendo o Event Storming, Glossário da Linguagem Ubíqua e Modelagem C4 até o nível 3 encontra-se armazenada na pasta docs/ddd/ do repositório.