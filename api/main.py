from fastapi import FastAPI
from db import get_connection

app = FastAPI()


@app.get("/")
def home():
    return {"mensagem": "BookingHub funcionando!"}


@app.get("/voos/disponiveis")
def voos_disponiveis(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            f.id,
            f.flight_number,
            origem.code AS origem,
            destino.code AS destino,
            f.departure_time,
            f.arrival_time,
            f.available_seats,
            f.price
        FROM flights f
        JOIN airports origem
            ON f.origin_airport_id = origem.id
        JOIN airports destino
            ON f.destination_airport_id = destino.id
        WHERE f.available_seats > 0
        ORDER BY f.departure_time
        LIMIT %s;
    """

    cur.execute(query, (limit,))
    rows = cur.fetchall()

    voos = []

    for row in rows:
        voos.append({
            "id": row[0],
            "flight_number": row[1],
            "origem": row[2],
            "destino": row[3],
            "departure_time": str(row[4]),
            "arrival_time": str(row[5]),
            "available_seats": row[6],
            "price": float(row[7])
        })

    cur.close()
    conn.close()

    return voos