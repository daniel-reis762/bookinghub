BEGIN;

SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

SELECT *
FROM flights
WHERE id = 1
FOR UPDATE;

UPDATE flights
SET available_seats = available_seats - 1
WHERE id = 1;

SELECT pg_sleep(10);

COMMIT;