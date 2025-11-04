import mysql.connector as msc
from mysql.connector import Error

def connect_db():
    try:
        pw = input("Enter MySQL password for connecting: ")

        con = msc.connect(
            host = "localhost",
            user = "root",
            password = pw 
            )

        if con.is_connected():
            print("Connected to MySQL server")

            cursor = con.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS bytevault;")
            print("Database 'bytevault' ok")

            cursor.close()
            con.close()

        con = msc.connect(
            host = "localhost",
            user = "root",
            password = pw,
            database = "bytevault"
        )

        return con
    
    except Error as e:
        print("Database connection error: ", e)
        return None
    

def setup_tables(con):
    try:
        cursor = con.cursor()

        master = """
        CREATE TABLE IF NOT EXISTS master (
            id INT PRIMARY KEY,
            master_pass BLOB NOT NULL
        ); """

        passwords = """
        CREATE TABLE IF NOT EXISTS passwords (
            id INT AUTO_INCREMENT PRIMARY KEY,
            site VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL,
            password BLOB NOT NULL
        ); """

        cursor.execute(master)
        cursor.execute(passwords)
        con.commit()
        cursor.close()
        print("Table created successfully")

    except Error as e:
        print("Table creation error: ", e)


if __name__ == "__main__":
    conn = connect_db()
    if conn:
        setup_tables(conn)
        conn.close()
        print("Database setup complete")