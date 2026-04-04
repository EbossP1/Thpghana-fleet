import psycopg, bcrypt, os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fleetuser:fleetpass@localhost:5432/fleetdb")

def init():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, "schema.sql")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            with open(schema_path, "r") as f:
                cur.execute(f.read())
            pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
            cur.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, role)
                VALUES ('admin', 'admin@thp-ghana.org', %s, 'Eric', 'Koomson', 'admin')
                ON CONFLICT (username) DO NOTHING
            """, (pw,))
            conn.commit()
    print("✅ Database initialised successfully")
    print("   Login: admin / admin123")

if __name__ == "__main__":
    init()
