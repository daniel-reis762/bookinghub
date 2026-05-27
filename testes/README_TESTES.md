# Testes de Concorrência e Isolamento

Os testes desta pasta demonstram:

- Controle de concorrência
- Locks pessimistas com FOR UPDATE
- Nível de isolamento SERIALIZABLE
- Retry logic
- Prevenção de overbooking

## Como executar

Abrir dois terminais simultaneamente:

```bash
docker exec -it bookinghub-db-1 psql -U booking -d bookinghub
```

No primeiro terminal:

```sql
\i testes/teste_isolamento.sql
```

Enquanto o primeiro terminal estiver executando, executar no segundo terminal:

```sql
BEGIN;

UPDATE flights
SET available_seats = available_seats - 1
WHERE id = 1;

COMMIT;
```

O segundo terminal ficará bloqueado até o término da primeira transação, demonstrando o funcionamento dos locks e do isolamento SERIALIZABLE.