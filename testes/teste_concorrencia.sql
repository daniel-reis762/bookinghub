-- Teste de concorrência para demonstrar lock com FOR UPDATE
-- Objetivo: simular uma reserva de voo segurando a linha bloqueada por alguns segundos.

BEGIN;

SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

SELECT id, flight_number, available_seats
FROM flights
WHERE id = 1
FOR UPDATE;

UPDATE flights
SET available_seats = available_seats - 1
WHERE id = 1
AND available_seats > 0;

SELECT pg_sleep(15);

COMMIT;