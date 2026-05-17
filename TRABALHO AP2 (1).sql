ALTER TABLE flights
ADD CONSTRAINT chk_different_airports
CHECK (origin_airport_id <> destination_airport_id);

ALTER TABLE flights
ADD CONSTRAINT uq_flight_number_departure
UNIQUE (flight_number, departure_time);


CREATE INDEX idx_flights_search
ON flights (
    origin_airport_id,
    destination_airport_id,
    departure_time
);

SELECT conname
FROM pg_constraint
WHERE conrelid = 'flight_reservations'::regclass
AND contype = 'u';

ALTER TABLE flight_reservations
DROP CONSTRAINT flight_reservations_flight_id_seat_number_key;

CREATE UNIQUE INDEX uq_active_seat
ON flight_reservations(flight_id, seat_number)
WHERE status1 != 'cancelled';

ALTER TABLE rooms
ADD COLUMN created_at TIMESTAMP DEFAULT NOW();

ALTER TABLE rooms
ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_rooms_updated_at
BEFORE UPDATE ON rooms
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
-- =====================================================
-- FUNÇÃO GENÉRICA
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =====================================================
-- HOTELS
-- =====================================================

ALTER TABLE hotels
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

CREATE TRIGGER trg_hotels_updated_at
BEFORE UPDATE ON hotels
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- ROOMS
-- =====================================================

ALTER TABLE rooms
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

CREATE TRIGGER trg_rooms_updated_at
BEFORE UPDATE ON rooms
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- FLIGHTS
-- =====================================================

ALTER TABLE flights
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

CREATE TRIGGER trg_flights_updated_at
BEFORE UPDATE ON flights
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- CUSTOMERS
-- =====================================================

ALTER TABLE customers
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

CREATE TRIGGER trg_customers_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- FLIGHT_RESERVATIONS
-- =====================================================

ALTER TABLE flight_reservations
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

CREATE TRIGGER trg_flight_reservations_updated_at
BEFORE UPDATE ON flight_reservations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- HOTEL_RESERVATIONS
-- =====================================================

ALTER TABLE hotel_reservations
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

CREATE TRIGGER trg_hotel_reservations_updated_at
BEFORE UPDATE ON hotel_reservations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- PAYMENTS
-- =====================================================

ALTER TABLE payments
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

CREATE TRIGGER trg_payments_updated_at
BEFORE UPDATE ON payments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

	CREATE EXTENSION IF NOT EXISTS btree_gist;



ALTER TABLE hotel_reservations
ADD CONSTRAINT no_overlapping_reservations
EXCLUDE USING gist (
    room_id WITH =,
    daterange(check_in, check_out, '[)') WITH &&
)
WHERE (status1 != 'cancelled');

SELECT conname
FROM pg_constraint
WHERE conrelid = 'rooms'::regclass
AND contype = 'f';

ALTER TABLE rooms
DROP CONSTRAINT rooms_hotel_id_fkey;

ALTER TABLE rooms
ADD CONSTRAINT rooms_hotel_id_fkey
FOREIGN KEY (hotel_id)
REFERENCES hotels(id)
ON DELETE CASCADE;