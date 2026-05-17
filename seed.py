"""
BookingHub — seed.py
Carrega os CSVs base e completa com dados gerados até atingir 10.000 registros.

Dependências: psycopg2, stdlib (random, datetime, csv, etc.)
Uso:
    python seed.py

Variável de ambiente (opcional):
    DATABASE_URL=postgresql://booking:secret@localhost:5432/bookinghub
"""

import csv
import os
import random
import string
import datetime
import sys

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    sys.exit("psycopg2 não encontrado. Instale com: pip install psycopg2-binary")

# ── Conexão ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://booking:secret@localhost:5432/bookinghub"
)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False
cur = conn.cursor()

# ── Helpers ───────────────────────────────────────────────────────────────────
def rand_cpf():
    d = [random.randint(0, 9) for _ in range(11)]
    return f"{d[0]}{d[1]}{d[2]}.{d[3]}{d[4]}{d[5]}.{d[6]}{d[7]}{d[8]}-{d[9]}{d[10]}"

def rand_phone():
    ddd = random.choice([11,21,31,41,51,61,71,81,85,62,67,92,96,98])
    num = random.randint(90000000, 99999999)
    return f"({ddd}) 9{num}"

def rand_str(length=8):
    return "".join(random.choices(string.ascii_lowercase, k=length))

def rand_date(start, end):
    delta = end - start
    return start + datetime.timedelta(days=random.randint(0, delta.days))

def rand_ts(start, end):
    delta = int((end - start).total_seconds())
    return start + datetime.timedelta(seconds=random.randint(0, delta))

PRIMEIRO_NOMES = [
    "Ana","Bruno","Carla","Diego","Eliane","Felipe","Gabriela","Henrique",
    "Isabela","João","Karina","Lucas","Mariana","Nicolas","Olivia","Paulo",
    "Quezia","Rafael","Sara","Thiago","Ursula","Victor","Wendy","Ximena",
    "Yasmin","Zara","Mateus","Larissa","Fernando","Beatriz","Ricardo","Julia",
    "Eduardo","Leticia","Gustavo","Amanda","Leonardo","Patricia","Rodrigo","Camila"
]
SOBRENOMES = [
    "Silva","Santos","Oliveira","Souza","Lima","Costa","Ferreira","Alves",
    "Pereira","Carvalho","Nascimento","Melo","Barbosa","Ribeiro","Rocha",
    "Freitas","Gomes","Martins","Dias","Castro","Mendes","Cardoso","Araujo",
    "Nunes","Teixeira","Moreira","Rodrigues","Lopes","Cunha","Pinto","Vieira"
]

def rand_name():
    return f"{random.choice(PRIMEIRO_NOMES)} {random.choice(SOBRENOMES)}"

AIRLINE_PREFIXES = ["LA","G3","AD","JJ","O6","2Z","TM","AV","CM","AM"]
FLIGHT_SUFFIXES  = list(range(1000, 9999))

HOTEL_NAMES = [
    "Ibis","Pullman","Mercure","Novotel","Holiday Inn","Sheraton","Marriott",
    "Hilton","Intercontinental","Best Western","Quality","Comfort Inn",
    "Golden Tulip","Windsor","Bristol","Slaviero","Blue Tree","Transamerica"
]
HOTEL_SUFFIX = ["Express","Premium","Plus","Grand","Select","Boutique","Suites","Resort"]

CIDADES = [
    ("São Paulo","Brasil"),("Rio de Janeiro","Brasil"),("Brasília","Brasil"),
    ("Fortaleza","Brasil"),("Salvador","Brasil"),("Recife","Brasil"),
    ("Manaus","Brasil"),("Belém","Brasil"),("Porto Alegre","Brasil"),
    ("Curitiba","Brasil"),("Goiânia","Brasil"),("Florianópolis","Brasil"),
    ("Maceió","Brasil"),("Natal","Brasil"),("Teresina","Brasil"),
    ("Campo Grande","Brasil"),("João Pessoa","Brasil"),("Aracaju","Brasil"),
]

AIRPORT_DATA = [
    (1,"GRU","Aeroporto Internacional de Guarulhos","Guarulhos","Brasil"),
    (2,"CGH","Aeroporto de Congonhas","São Paulo","Brasil"),
    (3,"SDU","Aeroporto Santos Dumont","Rio de Janeiro","Brasil"),
    (4,"GIG","Aeroporto Internacional do Galeão","Rio de Janeiro","Brasil"),
    (5,"BSB","Aeroporto Internacional de Brasília","Brasília","Brasil"),
    (6,"SSA","Aeroporto Internacional de Salvador","Salvador","Brasil"),
    (7,"FOR","Aeroporto Internacional Pinto Martins","Fortaleza","Brasil"),
    (8,"REC","Aeroporto Internacional do Recife","Recife","Brasil"),
    (9,"POA","Aeroporto Internacional Salgado Filho","Porto Alegre","Brasil"),
    (10,"CWB","Aeroporto Internacional Afonso Pena","Curitiba","Brasil"),
]

# ── Limpar tabelas (ordem inversa de FK) ──────────────────────────────────────
print("🗑  Limpando tabelas...")
for t in ["payments","hotel_reservations","flight_reservations",
          "rooms","flights","customers","hotels","airports"]:
    cur.execute(f"TRUNCATE {t} RESTART IDENTITY CASCADE")
conn.commit()

# ─────────────────────────────────────────────────────────────────────────────
# 1. AIRPORTS  (fixo — 10 registros dos CSVs)
# ─────────────────────────────────────────────────────────────────────────────
print("✈  Inserindo airports...")
execute_values(cur,
    "INSERT INTO airports (id,code,name,city,country) VALUES %s",
    AIRPORT_DATA
)
cur.execute("SELECT setval('airports_id_seq', (SELECT MAX(id) FROM airports))")
conn.commit()
airport_ids = [r[0] for r in AIRPORT_DATA]

# ─────────────────────────────────────────────────────────────────────────────
# 2. HOTELS  (12 CSV + gerados até 200)
# ─────────────────────────────────────────────────────────────────────────────
print("🏨  Inserindo hotels...")
CSV_HOTELS = "airports.csv"  # caminho relativo — ajuste se necessário

hotel_rows = []
csv_path = os.path.join(os.path.dirname(__file__), "airports.csv")

# Lê CSV de hotéis
hotels_csv_path = os.path.join(os.path.dirname(__file__), "hotels.csv")
with open(hotels_csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hotel_rows.append((
            int(row["id"]), row["name"], row["city"], row["country"],
            int(row["stars"]), row["address"]
        ))

# Gera hotéis extras até 200
existing_hotel_ids = {r[0] for r in hotel_rows}
next_hotel_id = max(existing_hotel_ids) + 1
while len(hotel_rows) < 200:
    cidade, pais = random.choice(CIDADES)
    nome = f"{random.choice(HOTEL_NAMES)} {cidade} {random.choice(HOTEL_SUFFIX)}"
    stars = random.randint(2, 5)
    rua = f"Av. {rand_name()} {random.randint(100,9999)}"
    hotel_rows.append((next_hotel_id, nome, cidade, pais, stars, rua))
    next_hotel_id += 1

execute_values(cur,
    "INSERT INTO hotels (id,name,city,country,stars,address) VALUES %s",
    hotel_rows
)
cur.execute("SELECT setval('hotels_id_seq', (SELECT MAX(id) FROM hotels))")
conn.commit()
hotel_ids = [r[0] for r in hotel_rows]

# ─────────────────────────────────────────────────────────────────────────────
# 3. CUSTOMERS  (12 CSV + gerados até 3000)
# ─────────────────────────────────────────────────────────────────────────────
print("👤  Inserindo customers...")
customer_rows = []
customers_csv_path = os.path.join(os.path.dirname(__file__), "customers.csv")
with open(customers_csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        customer_rows.append((
            int(row["id"]), row["name"], row["email"], row["cpf"],
            row["phone"], row["created_at"]
        ))

used_emails = {r[2] for r in customer_rows}
used_cpfs   = {r[3] for r in customer_rows}
next_cust_id = max(r[0] for r in customer_rows) + 1
created_start = datetime.datetime(2023, 1, 1)
created_end   = datetime.datetime(2025, 12, 31)

while len(customer_rows) < 3000:
    name  = rand_name()
    email = f"{rand_str(6)}.{rand_str(4)}@{random.choice(['gmail','outlook','yahoo','email'])}.com"
    cpf   = rand_cpf()
    if email in used_emails or cpf in used_cpfs:
        continue
    used_emails.add(email)
    used_cpfs.add(cpf)
    phone = rand_phone()
    ts    = rand_ts(created_start, created_end)
    customer_rows.append((next_cust_id, name, email, cpf, phone, ts))
    next_cust_id += 1

execute_values(cur,
    "INSERT INTO customers (id,name,email,cpf,phone,created_at) VALUES %s",
    customer_rows
)
cur.execute("SELECT setval('customers_id_seq', (SELECT MAX(id) FROM customers))")
conn.commit()
customer_ids = [r[0] for r in customer_rows]

# ─────────────────────────────────────────────────────────────────────────────
# 4. FLIGHTS  (15 CSV + gerados até 2000)
# ─────────────────────────────────────────────────────────────────────────────
print("🛫  Inserindo flights...")
flight_rows = []
flights_csv_path = os.path.join(os.path.dirname(__file__), "flights.csv")
with open(flights_csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        flight_rows.append((
            int(row["id"]), row["flight_number"],
            int(row["origin_airport_id"]), int(row["destination_airport_id"]),
            row["departure_time"], row["arrival_time"],
            int(row["total_seats"]), int(row["available_seats"]),
            float(row["price"])
        ))

used_flight_nums = {r[1] for r in flight_rows}
next_flight_id   = max(r[0] for r in flight_rows) + 1
dep_start = datetime.datetime(2024, 6, 1)
dep_end   = datetime.datetime(2026, 12, 31)

while len(flight_rows) < 2000:
    prefix = random.choice(AIRLINE_PREFIXES)
    num    = f"{prefix}{random.choice(FLIGHT_SUFFIXES)}"
    orig, dest = random.sample(airport_ids, 2)
    dep  = rand_ts(dep_start, dep_end).replace(minute=random.choice([0,15,30,45]), second=0)
    dur  = datetime.timedelta(hours=random.randint(1,6), minutes=random.choice([0,20,40]))
    arr  = dep + dur
    total = random.choice([120,144,160,174,180,200,220])
    avail = random.randint(0, total)
    price = round(random.uniform(199, 2499), 2)
    flight_rows.append((next_flight_id, num, orig, dest,
                        dep, arr, total, avail, price))
    next_flight_id += 1

execute_values(cur,
    """INSERT INTO flights
       (id,flight_number,origin_airport_id,destination_airport_id,
        departure_time,arrival_time,total_seats,available_seats,price)
       VALUES %s""",
    flight_rows
)
cur.execute("SELECT setval('flights_id_seq', (SELECT MAX(id) FROM flights))")
conn.commit()
flight_ids = [r[0] for r in flight_rows]

# ─────────────────────────────────────────────────────────────────────────────
# 5. ROOMS  (30 CSV + gerados até 1000)
# ─────────────────────────────────────────────────────────────────────────────
print("🛏  Inserindo rooms...")
room_rows = []
rooms_csv_path = os.path.join(os.path.dirname(__file__), "rooms.csv")
with open(rooms_csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        room_rows.append((
            int(row["id"]), int(row["hotel_id"]), row["room_number"],
            row["type"], int(row["capacity"]), float(row["price_per_night"])
        ))

# controla (hotel_id, room_number) únicos
used_room_keys = {(r[1], r[2]) for r in room_rows}
next_room_id   = max(r[0] for r in room_rows) + 1
ROOM_TYPES     = [("single",1,0.5),("double",2,0.35),("suite",4,0.15)]

while len(room_rows) < 1000:
    hid = random.choice(hotel_ids)
    rnum = str(random.randint(100, 999))
    if (hid, rnum) in used_room_keys:
        continue
    used_room_keys.add((hid, rnum))
    rtype, cap, _ = random.choices(ROOM_TYPES, weights=[0.5,0.35,0.15])[0]
    price = round(random.uniform(150, 1800), 2)
    room_rows.append((next_room_id, hid, rnum, rtype, cap, price))
    next_room_id += 1

execute_values(cur,
    "INSERT INTO rooms (id,hotel_id,room_number,type,capacity,price_per_night) VALUES %s",
    room_rows
)
cur.execute("SELECT setval('rooms_id_seq', (SELECT MAX(id) FROM rooms))")
conn.commit()
room_ids = [r[0] for r in room_rows]

# ─────────────────────────────────────────────────────────────────────────────
# 6. FLIGHT_RESERVATIONS  (15 CSV + gerados até 4000)
# ─────────────────────────────────────────────────────────────────────────────
print("📋  Inserindo flight_reservations...")
fr_rows = []
fr_csv_path = os.path.join(os.path.dirname(__file__), "flight_reservations.csv")
with open(fr_csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        fr_rows.append((
            int(row["id"]), int(row["customer_id"]), int(row["flight_id"]),
            row["seat_number"], row["status"], row["created_at"], row["updated_at"]
        ))

used_seats    = {(r[2], r[3]) for r in fr_rows}   # (flight_id, seat_number)
next_fr_id    = max(r[0] for r in fr_rows) + 1
STATUSES_FR   = ["confirmed","confirmed","confirmed","pending","cancelled"]
ts_base       = datetime.datetime(2024, 1, 1)
ts_end        = datetime.datetime(2026, 5, 15)

while len(fr_rows) < 4000:
    cid = random.choice(customer_ids)
    fid = random.choice(flight_ids)
    row_num = random.randint(1, 40)
    col     = random.choice(list("ABCDEF"))
    seat    = f"{row_num}{col}"
    if (fid, seat) in used_seats:
        continue
    used_seats.add((fid, seat))
    status = random.choice(STATUSES_FR)
    ts = rand_ts(ts_base, ts_end)
    fr_rows.append((next_fr_id, cid, fid, seat, status, ts, ts))
    next_fr_id += 1

execute_values(cur,
    """INSERT INTO flight_reservations
       (id,customer_id,flight_id,seat_number,status,created_at,updated_at)
       VALUES %s""",
    fr_rows
)
cur.execute("SELECT setval('flight_reservations_id_seq', (SELECT MAX(id) FROM flight_reservations))")
conn.commit()
fr_ids_confirmed = [(r[0], r[2]) for r in fr_rows if r[4] in ("confirmed","pending")]

# ─────────────────────────────────────────────────────────────────────────────
# 7. HOTEL_RESERVATIONS  (12 CSV + gerados até 3000)
# ─────────────────────────────────────────────────────────────────────────────
print("🏩  Inserindo hotel_reservations...")
hr_rows = []
hr_csv_path = os.path.join(os.path.dirname(__file__), "hotel_reservations.csv")

# mapa room_id -> price_per_night
room_price = {r[0]: r[5] for r in room_rows}

with open(hr_csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        hr_rows.append((
            int(row["id"]), int(row["customer_id"]), int(row["room_id"]),
            row["check_in"], row["check_out"], row["status"],
            float(row["total_price"]), row["created_at"]
        ))

# controle simples de conflito por (room_id, check_in, check_out)
room_intervals: dict[int, list] = {}
for r in hr_rows:
    rid = r[2]
    ci  = datetime.date.fromisoformat(str(r[3])[:10])
    co  = datetime.date.fromisoformat(str(r[4])[:10])
    room_intervals.setdefault(rid, []).append((ci, co))

def has_conflict(rid, ci, co):
    for existing_ci, existing_co in room_intervals.get(rid, []):
        if ci < existing_co and co > existing_ci:
            return True
    return False

next_hr_id  = max(r[0] for r in hr_rows) + 1
STATUSES_HR = ["confirmed","confirmed","confirmed","pending","cancelled"]
checkin_start = datetime.date(2024, 6, 1)
checkin_end   = datetime.date(2026, 12, 30)
attempts = 0

while len(hr_rows) < 3000 and attempts < 60000:
    attempts += 1
    cid  = random.choice(customer_ids)
    rid  = random.choice(room_ids)
    ci   = rand_date(checkin_start, checkin_end)
    nights = random.randint(1, 14)
    co   = ci + datetime.timedelta(days=nights)
    status = random.choice(STATUSES_HR)
    if status != "cancelled" and has_conflict(rid, ci, co):
        continue
    pnite = room_price.get(rid, 300.0)
    total = round(pnite * nights, 2)
    ts    = rand_ts(datetime.datetime(2024,1,1), datetime.datetime(2026,5,15))
    hr_rows.append((next_hr_id, cid, rid, ci, co, status, total, ts))
    room_intervals.setdefault(rid, []).append((ci, co))
    next_hr_id += 1

execute_values(cur,
    """INSERT INTO hotel_reservations
       (id,customer_id,room_id,check_in,check_out,status,total_price,created_at)
       VALUES %s""",
    hr_rows
)
cur.execute("SELECT setval('hotel_reservations_id_seq', (SELECT MAX(id) FROM hotel_reservations))")
conn.commit()
hr_ids = [(r[0], r[5]) for r in hr_rows]   # (id, status)

# ─────────────────────────────────────────────────────────────────────────────
# 8. PAYMENTS  (24 CSV + gerados para todas as reservas restantes)
# ─────────────────────────────────────────────────────────────────────────────
print("💳  Inserindo payments...")
pay_rows = []
pay_csv_path = os.path.join(os.path.dirname(__file__), "payments.csv")
with open(pay_csv_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        pay_rows.append((
            int(row["id"]), row["reservation_type"], int(row["reservation_id"]),
            float(row["amount"]), row["status"], row["payment_method"], row["created_at"]
        ))

already_paid_flight = {r[2] for r in pay_rows if r[1] == "flight"}
already_paid_hotel  = {r[2] for r in pay_rows if r[1] == "hotel"}
next_pay_id = max(r[0] for r in pay_rows) + 1
METHODS = ["credit_card","credit_card","pix","pix","debit_card","bank_transfer"]

def status_to_pay(res_status):
    if res_status == "confirmed": return "paid"
    if res_status == "cancelled": return "refunded"
    return "pending"

# pagamentos para flight_reservations
for fr_id, fid in fr_ids_confirmed:
    if fr_id in already_paid_flight:
        continue
    # busca status da reserva
    res_status = next((r[4] for r in fr_rows if r[0] == fr_id), "pending")
    price = next((r[8] for r in flight_rows if r[0] == fid), 499.0)
    pay_rows.append((
        next_pay_id, "flight", fr_id,
        round(price, 2), status_to_pay(res_status),
        random.choice(METHODS),
        rand_ts(datetime.datetime(2024,1,1), datetime.datetime(2026,5,15))
    ))
    next_pay_id += 1

# pagamentos para hotel_reservations
for hr_id, hr_status in hr_ids:
    if hr_id in already_paid_hotel:
        continue
    total = next((r[6] for r in hr_rows if r[0] == hr_id), 500.0)
    pay_rows.append((
        next_pay_id, "hotel", hr_id,
        round(total, 2), status_to_pay(hr_status),
        random.choice(METHODS),
        rand_ts(datetime.datetime(2024,1,1), datetime.datetime(2026,5,15))
    ))
    next_pay_id += 1

execute_values(cur,
    """INSERT INTO payments
       (id,reservation_type,reservation_id,amount,status,payment_method,created_at)
       VALUES %s""",
    pay_rows
)
cur.execute("SELECT setval('payments_id_seq', (SELECT MAX(id) FROM payments))")
conn.commit()

# ─────────────────────────────────────────────────────────────────────────────
# Resumo final
# ─────────────────────────────────────────────────────────────────────────────
cur.execute("""
    SELECT 'airports' AS t, COUNT(*) FROM airports UNION ALL
    SELECT 'hotels',        COUNT(*) FROM hotels UNION ALL
    SELECT 'customers',     COUNT(*) FROM customers UNION ALL
    SELECT 'flights',       COUNT(*) FROM flights UNION ALL
    SELECT 'rooms',         COUNT(*) FROM rooms UNION ALL
    SELECT 'flight_reservations', COUNT(*) FROM flight_reservations UNION ALL
    SELECT 'hotel_reservations',  COUNT(*) FROM hotel_reservations UNION ALL
    SELECT 'payments',      COUNT(*) FROM payments
    ORDER BY 1
""")
total = 0
print("\n📊  Registros inseridos:")
print(f"  {'Tabela':<25} {'Registros':>10}")
print(f"  {'-'*35}")
for row in cur.fetchall():
    print(f"  {row[0]:<25} {row[1]:>10,}")
    total += row[1]
print(f"  {'-'*35}")
print(f"  {'TOTAL':<25} {total:>10,}")

cur.close()
conn.close()
print("\n✅  Seed concluído com sucesso!")
