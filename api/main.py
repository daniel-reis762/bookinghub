from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import get_connection

app = FastAPI()
class ReservaVoo(BaseModel):
    customer_id: int
    flight_id: int
    seat_number: str

class Pagamento(BaseModel):
    reservation_type: str
    reservation_id: int
    amount: float
    payment_method: str


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




@app.post("/reservas/voo")
def criar_reserva_voo(reserva: ReservaVoo):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("BEGIN;")

        cur.execute("""
            SELECT available_seats
            FROM flights
            WHERE id = %s
            FOR UPDATE;
        """, (reserva.flight_id,))

        voo = cur.fetchone()

        if voo is None:
            raise HTTPException(status_code=404, detail="Voo não encontrado")

        available_seats = voo[0]

        if available_seats <= 0:
            raise HTTPException(
                status_code=409,
                detail="Não há assentos disponíveis"
            )

        cur.execute("""
            SELECT id
            FROM flight_reservations
            WHERE flight_id = %s
            AND seat_number = %s
            AND status != 'cancelled';
        """, (reserva.flight_id, reserva.seat_number))

        assento = cur.fetchone()

        if assento:
            raise HTTPException(
                status_code=409,
                detail="Assento já ocupado"
            )

        cur.execute("""
            INSERT INTO flight_reservations
            (customer_id, flight_id, seat_number, status)
            VALUES (%s, %s, %s, 'confirmed')
            RETURNING id;
        """, (
            reserva.customer_id,
            reserva.flight_id,
            reserva.seat_number
        ))

        reserva_id = cur.fetchone()[0]

        cur.execute("""
            UPDATE flights
            SET available_seats = available_seats - 1
            WHERE id = %s;
        """, (reserva.flight_id,))

        conn.commit()

        return {
            "mensagem": "Reserva criada com sucesso",
            "reserva_id": reserva_id
        }

    except HTTPException as e:
        conn.rollback()
        raise e

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        cur.close()
        conn.close()





@app.get("/hoteis/disponiveis")
def hoteis_disponiveis(check_in: str, check_out: str, city: str = None, limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT DISTINCT
            h.id,
            h.name,
            h.city,
            h.country,
            h.stars,
            h.address
        FROM hotels h
        JOIN rooms r ON r.hotel_id = h.id
        WHERE (%s IS NULL OR h.city = %s)
        AND r.id NOT IN (
            SELECT hr.room_id
            FROM hotel_reservations hr
            WHERE hr.status != 'cancelled'
            AND hr.check_in < %s
            AND hr.check_out > %s
        )
        ORDER BY h.stars DESC
        LIMIT %s;
    """

    cur.execute(query, (city, city, check_out, check_in, limit))
    rows = cur.fetchall()

    hoteis = []

    for row in rows:
        hoteis.append({
            "id": row[0],
            "name": row[1],
            "city": row[2],
            "country": row[3],
            "stars": row[4],
            "address": row[5],
        })

    cur.close()
    conn.close()

    return hoteis






@app.delete("/reservas/{reserva_id}")
def cancelar_reserva_voo(reserva_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN;")

        cur.execute("""
            SELECT flight_id, status
            FROM flight_reservations
            WHERE id = %s
            FOR UPDATE;
        """, (reserva_id,))

        reserva = cur.fetchone()

        if reserva is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")

        flight_id = reserva[0]
        status = reserva[1]

        if status == "cancelled":
            raise HTTPException(status_code=409, detail="Reserva já está cancelada")

        cur.execute("""
            UPDATE flight_reservations
            SET status = 'cancelled',
                updated_at = NOW()
            WHERE id = %s;
        """, (reserva_id,))

        cur.execute("""
            UPDATE flights
            SET available_seats = available_seats + 1
            WHERE id = %s;
        """, (flight_id,))

        conn.commit()

        return {"mensagem": "Reserva cancelada com sucesso"}

    except HTTPException as e:
        conn.rollback()
        raise e

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()





@app.post("/pagamentos")
def registrar_pagamento(pagamento: Pagamento):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN;")

        if pagamento.reservation_type == "flight":
            cur.execute("""
                SELECT id, status
                FROM flight_reservations
                WHERE id = %s
                FOR UPDATE;
            """, (pagamento.reservation_id,))
        elif pagamento.reservation_type == "hotel":
            cur.execute("""
                SELECT id, status
                FROM hotel_reservations
                WHERE id = %s
                FOR UPDATE;
            """, (pagamento.reservation_id,))
        else:
            raise HTTPException(status_code=400, detail="Tipo de reserva inválido")

        reserva = cur.fetchone()

        if reserva is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")

        if reserva[1] == "cancelled":
            raise HTTPException(status_code=409, detail="Reserva cancelada não pode ser paga")

        cur.execute("""
            INSERT INTO payments (
                reservation_type,
                reservation_id,
                amount,
                status,
                payment_method
            )
            VALUES (%s, %s, %s, 'paid', %s)
            RETURNING id;
        """, (
            pagamento.reservation_type,
            pagamento.reservation_id,
            pagamento.amount,
            pagamento.payment_method,
        ))

        pagamento_id = cur.fetchone()[0]

        if pagamento.reservation_type == "flight":
            cur.execute("""
                UPDATE flight_reservations
                SET status = 'confirmed',
                    updated_at = NOW()
                WHERE id = %s;
            """, (pagamento.reservation_id,))
        else:
            cur.execute("""
                UPDATE hotel_reservations
                SET status = 'confirmed'
                WHERE id = %s;
            """, (pagamento.reservation_id,))

        conn.commit()

        return {
            "mensagem": "Pagamento registrado com sucesso",
            "pagamento_id": pagamento_id
        }

    except HTTPException as e:
        conn.rollback()
        raise e

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()