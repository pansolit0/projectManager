import mysql.connector

class DatabaseConnection:
    def __init__(self):
        self.host = "localhost"
        self.user = "steelwow"
        self.password = "Steelwow2"
        self.database = "gestion_tareas"

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return self.connection
        except mysql.connector.Error as error:
            print(f"Error al conectar a MySQL: {error}")
            return None

    def close(self):
        if self.connection.is_connected():
            self.connection.close()
