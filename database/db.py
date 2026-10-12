import os
from dotenv import load_dotenv

load_dotenv()

TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if TURSO_URL and TURSO_TOKEN:
    # Si estamos en Render, usamos el driver de la Nube
    import libsql_experimental as sqlite3
    def get_db_connection():
        url = os.getenv("TURSO_DATABASE_URL")
        token = os.getenv("TURSO_AUTH_TOKEN")
    
        if url and token:
            import libsql_experimental
            return libsql_experimental.connect(database=url, auth_token=token)
        else:
            import sqlite3
            conn = sqlite3.connect("database.sqlite")
            conn.row_factory = sqlite3.Row
            return conn
    def dict_factory(cursor, row):
        return dict(zip([col[0] for col in cursor.description], row))
        conn.row_factory = dict_factory
        return conn
else:
    # Si estamos en tu PC, usamos el de siempre
    import sqlite3
    def get_db_connection():
        conn = sqlite3.connect('database.sqlite')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_comidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            fecha TEXT,
            descripcion TEXT,
            calorias INTEGER,
            proteinas INTEGER,
            carbohidratos INTEGER,
            grasas INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS garmin_cache (
            fecha TEXT PRIMARY KEY,
            calorias_quemadas INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_entrenamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            fecha TEXT,
            descripcion TEXT,
            calorias INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    print("🗄️ Base de datos (Local/Nube) inicializada y lista.")