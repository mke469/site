from db import get_connection

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabela articole
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articole (
            id SERIAL PRIMARY KEY,
            titlu TEXT NOT NULL,
            continut TEXT NOT NULL
        );
    """)

    # Tabela utilizatori
    cur.execute("""
        CREATE TABLE IF NOT EXISTS utilizatori (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            parola TEXT NOT NULL
        );
    """)

    # Tabela etichete
    cur.execute("""
        CREATE TABLE IF NOT EXISTS etichete (
            id SERIAL PRIMARY KEY,
            nume TEXT UNIQUE NOT NULL
        );
    """)

    # Tabela de legătură articole-etichete
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articole_etichete (
            articol_id INTEGER REFERENCES articole(id) ON DELETE CASCADE,
            eticheta_id INTEGER REFERENCES etichete(id) ON DELETE CASCADE,
            PRIMARY KEY (articol_id, eticheta_id)
        );
    """)

    # Inserare cont admin securizat
    cur.execute("""
        INSERT INTO utilizatori (username, parola)
        VALUES (
            'admin_a284c4',
            'scrypt:32768:8:1$MASf5IOSh4RQCQjB$caf1bb6d53946fae388bda12a152e9980c30e6cd8b2e9f3f5ce762343cf719125e0bac0999ec8c944a63453244f9681bc7607e49b466ebf8657ab0eb322aa452'
        )
        ON CONFLICT (username) DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Baza de date a fost inițializată cu succes.")

if __name__ == "__main__":
    init_db()