from fastapi import FastAPI
from db import get_connection

app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "BookingHub funcionando!"}

@app.get("/testar-banco")
def testar_banco():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT version();")
    resultado = cur.fetchone()

    cur.close()
    conn.close()

    return {"postgresql": resultado[0]}