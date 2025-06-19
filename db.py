import psycopg2

def get_connection():
    return psycopg2.connect(
        host="pg-377b54ee-tudorneacsu1-0f9c.d.aivencloud.com",
        dbname="defaultdb",
        user="avnadmin",
        password="AVNS_hkjEWKFcuzmPQdlZo7a",
        port=28304
    )
