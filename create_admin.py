from werkzeug.security import generate_password_hash
from database import get_db_connection


full_name = "kenedy delacruz"
username = "admin"
email = "kenedydelacruz15@example.com"
password = "kenedy0215"


connection = None
cursor = None

try:

    connection = get_db_connection()

    cursor = connection.cursor()

    password_hash = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (
            full_name,
            username,
            email,
            password_hash,
            role,
            is_active,
            store_id
        )
        VALUES (%s, %s, %s, %s, 'ADMIN', TRUE, NULL)
    """, (
        full_name,
        username,
        email,
        password_hash
    ))

    connection.commit()

    print("ADMIN account created successfully.")

except Exception as e:

    print("ERROR:", e)

finally:

    if cursor:
        cursor.close()

    if connection:
        connection.close()