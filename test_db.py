from database import get_db_connection


try:
    connection = get_db_connection()

    if connection.is_connected():
        print("SUCCESS: Connected to MySQL!")

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")

        result = cursor.fetchone()

        print("Current database:", result[0])

        cursor.close()
        connection.close()

except Exception as e:
    print("FAILED:", e)