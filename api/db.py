import psycopg2

def get_connection():
    return psycopg2.connect(
        host="db",
        database="bookinghub",
        user="booking",
        password="secret",
        port=5432
    )