-- ============================================================
-- BookingHub — schema.sql
-- PostgreSQL 14+
-- ============================================================

DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS hotel_reservations CASCADE;
DROP TABLE IF EXISTS flight_reservations CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;
DROP TABLE IF EXISTS flights CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS hotels CASCADE;
DROP TABLE IF EXISTS airports CASCADE;

-- ------------------------------------------------------------
-- 1. airports
-- ------------------------------------------------------------
CREATE TABLE airports (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);

-- ------------------------------------------------------------
-- 2. hotels
-- ------------------------------------------------------------
CREATE TABLE hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    stars SMALLINT NOT NULL CHECK (stars BETWEEN 1 AND 5),
    address VARCHAR(255)
);

-- ------------------------------------------------------------
-- 3. customers
-- ------------------------------------------------------------
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 4. flights
-- ------------------------------------------------------------
CREATE TABLE flights (
    id SERIAL PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL UNIQUE,
    origin_airport_id INT NOT NULL REFERENCES airports(id),
    destination_airport_id INT NOT NULL REFERENCES airports(id),
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    total_seats INT NOT NULL CHECK (total_seats > 0),
    available_seats INT NOT NULL CHECK (available_seats >= 0),
    price NUMERIC(10,2) NOT NULL CHECK (price > 0),

    CONSTRAINT chk_seats CHECK (available_seats <= total_seats),
    CONSTRAINT chk_times CHECK (arrival_time > departure_time)
);

-- ------------------------------------------------------------
-- 5. rooms
-- ------------------------------------------------------------
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    hotel_id INT NOT NULL REFERENCES hotels(id),
    room_number VARCHAR(10) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('single','double','suite')),
    capacity SMALLINT NOT NULL CHECK (capacity > 0),
    price_per_night NUMERIC(10,2) NOT NULL CHECK (price_per_night > 0),

    UNIQUE (hotel_id, room_number)
);

-- ------------------------------------------------------------
-- 6. flight_reservations
-- ------------------------------------------------------------
CREATE TABLE flight_reservations (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    flight_id INT NOT NULL REFERENCES flights(id),
    seat_number VARCHAR(5) NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','confirmed','cancelled')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Permite reutilizar assento quando a reserva anterior estiver cancelada
CREATE UNIQUE INDEX idx_unique_active_flight_seat
ON flight_reservations (flight_id, seat_number)
WHERE status <> 'cancelled';

-- ------------------------------------------------------------
-- 7. hotel_reservations
-- ------------------------------------------------------------
CREATE TABLE hotel_reservations (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    room_id INT NOT NULL REFERENCES rooms(id),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','confirmed','cancelled')),
    total_price NUMERIC(10,2) NOT NULL CHECK (total_price >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_dates CHECK (check_out > check_in)
);

-- ------------------------------------------------------------
-- 8. payments
-- ------------------------------------------------------------
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    reservation_type VARCHAR(10) NOT NULL
        CHECK (reservation_type IN ('flight','hotel')),
    reservation_id INT NOT NULL,
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    status VARCHAR(15) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','paid','refunded','failed')),
    payment_method VARCHAR(20) NOT NULL
        CHECK (payment_method IN ('credit_card','debit_card','pix','bank_transfer')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES PARA CONSULTAS DO TRABALHO
-- ============================================================

-- C1: voos disponíveis com filtro por origem, destino, data e vagas
CREATE INDEX idx_airports_city
ON airports (city);

CREATE INDEX idx_flights_route_departure
ON flights (origin_airport_id, destination_airport_id, departure_time);

CREATE INDEX idx_flights_available_departure
ON flights (departure_time)
WHERE available_seats > 0;

-- C2: taxa de ocupação por voo
CREATE INDEX idx_flights_departure
ON flights (departure_time);

CREATE INDEX idx_fr_flight_status
ON flight_reservations (flight_id, status);

-- C3: quartos disponíveis sem conflito de datas
CREATE INDEX idx_rooms_hotel
ON rooms (hotel_id);

CREATE INDEX idx_hr_room_dates
ON hotel_reservations (room_id, check_in, check_out)
WHERE status <> 'cancelled';

-- C4: histórico completo do cliente
CREATE INDEX idx_fr_customer
ON flight_reservations (customer_id);

CREATE INDEX idx_hr_customer
ON hotel_reservations (customer_id);

CREATE INDEX idx_payments_reservation
ON payments (reservation_type, reservation_id);

-- ============================================================
-- FIM DO SCHEMA
-- ============================================================