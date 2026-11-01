# Sistema Integrado de Atendimento e Execução de Serviços - Oficina Mecânica

> **Tech Challenge — Fase 1 | Pós-Graduação em Arquitetura de Software (SOAT FIAP)**

---

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

## 6. Instruções para Execução Local
1. Clone o repositório e acesse a pasta raiz:
   ```powershell
   cd tech-challenge-oficina-mecanica
   