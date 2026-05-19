import random
from datetime import datetime, timedelta

import psycopg2
from faker import Faker

fake = Faker("pt_BR")

DB_CONFIG = {
    "host": "db",
    "database": "bookinghub",
    "user": "booking",
    "password": "secret",
    "port": 5432,
}


def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding("UTF8")
    return conn


def limpar_banco(cur):
    cur.execute("""
        TRUNCATE TABLE
            payments,
            hotel_reservations,
            flight_reservations,
            rooms,
            flights,
            customers,
            hotels,
            airports
        RESTART IDENTITY CASCADE;
    """)


def inserir_airports(cur, quantidade=50):
    cidades = [
        ("São Paulo", "Brasil"),
        ("Rio de Janeiro", "Brasil"),
        ("Fortaleza", "Brasil"),
        ("Recife", "Brasil"),
        ("Salvador", "Brasil"),
        ("Brasília", "Brasil"),
        ("Belo Horizonte", "Brasil"),
        ("Curitiba", "Brasil"),
        ("Porto Alegre", "Brasil"),
        ("Manaus", "Brasil"),
    ]

    airports = []

    for i in range(quantidade):
        city, country = random.choice(cidades)
        code = f"A{i + 1:03d}"
        name = f"Aeroporto {fake.company()}"

        cur.execute("""
            INSERT INTO airports (code, name, city, country)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (code, name, city, country))

        airports.append(cur.fetchone()[0])

    return airports


def inserir_customers(cur, quantidade=2000):
    customers = []

    for i in range(quantidade):
        cur.execute("""
            INSERT INTO customers (name, email, cpf, phone)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (
            fake.name(),
            f"cliente{i + 1}@email.com",
            fake.cpf(),
            fake.phone_number(),
        ))

        customers.append(cur.fetchone()[0])

    return customers


def inserir_hotels(cur, quantidade=500):
    cidades = [
        ("São Paulo", "Brasil"),
        ("Rio de Janeiro", "Brasil"),
        ("Fortaleza", "Brasil"),
        ("Recife", "Brasil"),
        ("Salvador", "Brasil"),
        ("Brasília", "Brasil"),
        ("Belo Horizonte", "Brasil"),
        ("Curitiba", "Brasil"),
        ("Porto Alegre", "Brasil"),
        ("Manaus", "Brasil"),
    ]

    hotels = []

    for _ in range(quantidade):
        city, country = random.choice(cidades)

        cur.execute("""
            INSERT INTO hotels (name, city, country, stars, address)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            f"Hotel {fake.company()}",
            city,
            country,
            random.randint(1, 5),
            fake.address(),
        ))

        hotels.append(cur.fetchone()[0])

    return hotels


def inserir_rooms(cur, hotels, quartos_por_hotel=10):
    rooms = []
    tipos = ["single", "double", "suite"]

    for hotel_id in hotels:
        for numero in range(1, quartos_por_hotel + 1):
            tipo = random.choice(tipos)

            if tipo == "single":
                capacity = 1
                price = random.uniform(120, 250)
            elif tipo == "double":
                capacity = 2
                price = random.uniform(200, 400)
            else:
                capacity = 4
                price = random.uniform(450, 900)

            cur.execute("""
                INSERT INTO rooms (hotel_id, room_number, type, capacity, price_per_night)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                hotel_id,
                str(numero),
                tipo,
                capacity,
                round(price, 2),
            ))

            rooms.append(cur.fetchone()[0])

    return rooms


def inserir_flights(cur, airports, quantidade=3000):
    flights = []

    for i in range(quantidade):
        origin = random.choice(airports)
        destination = random.choice(airports)

        while destination == origin:
            destination = random.choice(airports)

        departure_time = datetime.now() + timedelta(
            days=random.randint(-30, 120),
            hours=random.randint(0, 23),
        )
        arrival_time = departure_time + timedelta(hours=random.randint(1, 8))

        total_seats = random.choice([120, 150, 180, 220])
        available_seats = random.randint(0, total_seats)

        cur.execute("""
            INSERT INTO flights (
                flight_number,
                origin_airport_id,
                destination_airport_id,
                departure_time,
                arrival_time,
                total_seats,
                available_seats,
                price
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            f"BH{i + 1:05d}",
            origin,
            destination,
            departure_time,
            arrival_time,
            total_seats,
            available_seats,
            round(random.uniform(250, 1800), 2),
        ))

        flights.append(cur.fetchone()[0])

    return flights


def inserir_flight_reservations(cur, customers, flights, quantidade=4000):
    reservations = []
    assentos_usados = set()

    for _ in range(quantidade):
        customer_id = random.choice(customers)
        flight_id = random.choice(flights)

        seat_number = f"{random.randint(1, 40)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"

        tentativas = 0
        while (flight_id, seat_number) in assentos_usados and tentativas < 10:
            seat_number = f"{random.randint(1, 40)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
            tentativas += 1

        if (flight_id, seat_number) in assentos_usados:
            continue

        assentos_usados.add((flight_id, seat_number))

        status = random.choice(["pending", "confirmed", "cancelled"])

        created_at = datetime.now() - timedelta(days=random.randint(0, 90))
        updated_at = created_at + timedelta(days=random.randint(0, 5))

        cur.execute("""
            INSERT INTO flight_reservations (
                customer_id,
                flight_id,
                seat_number,
                status,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            customer_id,
            flight_id,
            seat_number,
            status,
            created_at,
            updated_at,
        ))

        reservations.append(cur.fetchone()[0])

    return reservations


def inserir_hotel_reservations(cur, customers, rooms, quantidade=3000):
    reservations = []

    for _ in range(quantidade):
        customer_id = random.choice(customers)
        room_id = random.choice(rooms)

        check_in = datetime.now().date() + timedelta(days=random.randint(-30, 120))
        noites = random.randint(1, 10)
        check_out = check_in + timedelta(days=noites)

        status = random.choice(["pending", "confirmed", "cancelled"])
        total_price = round(random.uniform(150, 3000), 2)

        cur.execute("""
            INSERT INTO hotel_reservations (
                customer_id,
                room_id,
                check_in,
                check_out,
                status,
                total_price,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            customer_id,
            room_id,
            check_in,
            check_out,
            status,
            total_price,
            datetime.now() - timedelta(days=random.randint(0, 90)),
        ))

        reservations.append(cur.fetchone()[0])

    return reservations


def inserir_payments(cur, flight_reservations, hotel_reservations):
    total = 0

    for reservation_id in flight_reservations:
        if random.random() < 0.75:
            cur.execute("""
                INSERT INTO payments (
                    reservation_type,
                    reservation_id,
                    amount,
                    status,
                    payment_method
                )
                VALUES (%s, %s, %s, %s, %s);
            """, (
                "flight",
                reservation_id,
                round(random.uniform(250, 1800), 2),
                random.choice(["pending", "paid", "refunded", "failed"]),
                random.choice(["credit_card", "debit_card", "pix", "bank_transfer"]),
            ))
            total += 1

    for reservation_id in hotel_reservations:
        if random.random() < 0.75:
            cur.execute("""
                INSERT INTO payments (
                    reservation_type,
                    reservation_id,
                    amount,
                    status,
                    payment_method
                )
                VALUES (%s, %s, %s, %s, %s);
            """, (
                "hotel",
                reservation_id,
                round(random.uniform(150, 3000), 2),
                random.choice(["pending", "paid", "refunded", "failed"]),
                random.choice(["credit_card", "debit_card", "pix", "bank_transfer"]),
            ))
            total += 1

    return total


def main():
    conn = get_connection()
    cur = conn.cursor()

    print("Limpando banco...")
    limpar_banco(cur)

    print("Inserindo aeroportos...")
    airports = inserir_airports(cur)

    print("Inserindo clientes...")
    customers = inserir_customers(cur)

    print("Inserindo hotéis...")
    hotels = inserir_hotels(cur)

    print("Inserindo quartos...")
    rooms = inserir_rooms(cur, hotels)

    print("Inserindo voos...")
    flights = inserir_flights(cur, airports)

    print("Inserindo reservas de voo...")
    flight_reservations = inserir_flight_reservations(cur, customers, flights)

    print("Inserindo reservas de hotel...")
    hotel_reservations = inserir_hotel_reservations(cur, customers, rooms)

    print("Inserindo pagamentos...")
    total_payments = inserir_payments(cur, flight_reservations, hotel_reservations)

    conn.commit()

    print("\nSeed executado com sucesso!")
    print(f"Aeroportos: {len(airports)}")
    print(f"Clientes: {len(customers)}")
    print(f"Hotéis: {len(hotels)}")
    print(f"Quartos: {len(rooms)}")
    print(f"Voos: {len(flights)}")
    print(f"Reservas de voo: {len(flight_reservations)}")
    print(f"Reservas de hotel: {len(hotel_reservations)}")
    print(f"Pagamentos: {total_payments}")
    print(f"Total aproximado: {len(airports) + len(customers) + len(hotels) + len(rooms) + len(flights) + len(flight_reservations) + len(hotel_reservations) + total_payments}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()