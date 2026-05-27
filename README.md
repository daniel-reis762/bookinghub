# BookingHub

BookingHub é um sistema de gerenciamento de reservas de voos e hotéis desenvolvido com PostgreSQL, FastAPI e Docker. O projeto foi criado para simular uma plataforma de turismo com alta concorrência, permitindo consultas, reservas, pagamentos e controle transacional em operações simultâneas.

O principal objetivo do sistema é demonstrar conceitos avançados de Banco de Dados, incluindo:

- Processamento de consultas
- Índices e otimização SQL
- Controle de concorrência
- Transações
- Recuperação de falhas
- Backup e restore

---

# Integrantes

- Carlos Daniel Reis da Silva
- Guilherme Mata Santos
- José Kayky Barbosa Coelho
---

# Tecnologias Utilizadas

- Python 3
- FastAPI
- PostgreSQL 16
- Docker
- Docker Compose
- psycopg2
- Faker

---

# Funcionalidades

## Sistema de Reservas

- Reservas de voos
- Reservas de hotéis
- Histórico de reservas
- Relatórios de ocupação
- Registro de pagamentos
- Cancelamento de reservas

## Banco de Dados

- Controle de concorrência com FOR UPDATE
- Transações SQL
- Rollback automático
- Índices para otimização
- EXPLAIN ANALYZE
- Backup e restore

## Infraestrutura

- Containers Docker
- API REST com FastAPI
- PostgreSQL integrado
- Documentação automática via Swagger

---

# Quick Start (Iniciação Rápida)

## Pré-requisitos

- Docker
- Docker Compose

---

# Como Executar o Projeto

## 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd bookinghub
```

## 2. Subir os containers

```bash
docker compose up -d --build
docker ps
```

## 3. Executar o seed

```bash
docker cp seed.py bookinghub-api-1:/app/seed.py
docker exec -it bookinghub-api-1 python seed.py
```

---

# Acessos

## Swagger

```txt
http://localhost:8000/docs
```

## Banco PostgreSQL

Host: localhost  
Porta: 5432  
Banco: bookinghub  
Usuário: booking  
Senha: secret
---

# Funcionalidades

## Consultas

- Buscar voos disponíveis
- Buscar hotéis disponíveis
- Consultar reservas dos clientes
- Relatório de ocupação

## Reservas

- Criar reserva de voo
- Criar reserva de hotel
- Cancelar reservas

## Pagamentos

- Registrar pagamentos de reservas

## Banco de Dados

- Controle de concorrência
- Transações SQL
- Locks com FOR UPDATE
- Índices para otimização
- Backup e restore

---

# Endpoints

## GET

```txt
/
/voos/disponiveis
/hoteis/disponiveis
/clientes/{cliente_id}/reservas
/relatorios/ocupacao
```

## POST

```txt
/reservas/voo
/reservas/hotel
/pagamentos
```

## DELETE

```txt
/reservas/{reserva_id}
```

---

# Seed

O sistema gera automaticamente mais de 20 mil registros para testes de:

- desempenho
- concorrência
- índices
- consultas SQL
- EXPLAIN ANALYZE

---

# Backup e Restore

## Gerar backup

```bash
docker exec -it bookinghub-db-1 pg_dump -U booking -d bookinghub -Fc -f /tmp/bookinghub.dump
docker cp bookinghub-db-1:/tmp/bookinghub.dump backup/bookinghub.dump
```

## Restaurar backup

```bash
docker cp backup/bookinghub.dump bookinghub-db-1:/tmp/bookinghub.dump
docker exec -it bookinghub-db-1 pg_restore -U booking -d bookinghub --clean --if-exists /tmp/bookinghub.dump
```

