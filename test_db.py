import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",              # உங்க MySQL username
        password="root", # install செய்யும் போது root password என்ன கொடுத்தீங்கோ அதை இங்கே போடு
        database="bank_db"        # உங்க database பெயர்
    )
    print("✅ Database connection successful!")
except mysql.connector.Error as err:
    print(f"❌ Error: {err}")
