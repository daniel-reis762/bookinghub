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





@app.get("/clientes/{cliente_id}/reservas")
def reservas_cliente(cliente_id: int):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 'voo' AS tipo,
               fr.id AS reserva_id,
               f.flight_number AS descricao,
               f.departure_time AS data,
               fr.status,
               p.amount,
               p.status AS pagamento_status
        FROM flight_reservations fr
        JOIN flights f ON f.id = fr.flight_id
        LEFT JOIN payments p
            ON p.reservation_id = fr.id
            AND p.reservation_type = 'flight'
        WHERE fr.customer_id = %s

        UNION ALL

        SELECT 'hotel' AS tipo,
               hr.id AS reserva_id,
               h.name AS descricao,
               hr.check_in AS data,
               hr.status,
               p.amount,
               p.status AS pagamento_status
        FROM hotel_reservations hr
        JOIN rooms r ON r.id = hr.room_id
        JOIN hotels h ON h.id = r.hotel_id
        LEFT JOIN payments p
            ON p.reservation_id = hr.id
            AND p.reservation_type = 'hotel'
        WHERE hr.customer_id = %s

        ORDER BY data DESC;
    """

    cur.execute(query, (cliente_id, cliente_id))
    rows = cur.fetchall()

    reservas = []

    for row in rows:
        reservas.append({
            "tipo": row[0],
            "reserva_id": row[1],
            "descricao": row[2],
            "data": str(row[3]),
            "status": row[4],
            "valor_pago": float(row[5]) if row[5] is not None else None,
            "status_pagamento": row[6]
        })

    cur.close()
    conn.close()

    return reservas