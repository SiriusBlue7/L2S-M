from flask import Flask, jsonify
import pymysql

app = Flask(__name__)
app.json.sort_keys = False
databaseIP = "database-service" #This is the IP of the database service. We have to change it to the correct IP of the database service.

def count_occurrences(rows, value):
    count = 0
    for row in rows:
        if row[0] == value:
            count += 1
    return count


def get_nodeIP(node):
    # Creamos la conexion a la base de datos
    db = pymysql.connect(host=databaseIP,user="l2sm",password="l2sm;",db="L2SM")
    cur = db.cursor()

    # Hacemos consulta a la base de datos para obtener la direccion IP del nodo
    consulta = "SELECT ip FROM switches WHERE node = %s "
    #table3 = "CREATE TABLE IF NOT EXISTS switches (openflowId TEXT, ip TEXT, node TEXT NOT NULL);"
    cur.execute(consulta,node)
    # Leemos la primera fila de los resultados y lo guardamos en la variable IP (si hubiese mas de un resultado usar fetchall())
    switchIP = cur.fetchone()
    # Como devuelve una tupla con un solo campo retornamos el valor de dentro de la tupla en vez de la tupla en si
    IP = switchIP[0]

    return IP

def get_Overlay():#This function is used to check if a node already has a connection with another node.
    #Count the number of elements in a table that match a given list of values.
    print("Hola")
    try:
        # Connect to the MySQL database
        print("Hola2")
        db = pymysql.connect(host=databaseIP,user="l2sm",password="l2sm;",db="L2SM")

        # Create a cursor object to execute SQL queries
        cur = db.cursor()
        #CREATE TABLES IF THEY DO NOT EXIST
        connections = "CREATE TABLE IF NOT EXISTS connections (node TEXT NOT NULL, connection TEXT NOT NULL);"
        #We create a table called connections with two columns: node and connection.
        cur.execute(connections) #We execute the query to create the table.
        db.commit()#We commit the changes to the database

        #Execute the query requesting all the values in the table connections.
        cur.execute("SELECT * FROM connections")

        # Fetch the result of the query
        rows = cur.fetchall()

        # Iterate over the rows and print the data
        rows = sorted(rows, key=lambda x: x[0]) #We sort the rows by the first element of the row.
        aux = "" # We create an auxiliar variable to store the value of the first element of the row.
        json=[] # We create a list to store the json object.
        for row in rows:
            if aux != row[0]: # Check if the value is the different from the previous value.
                node = {
                "name": row[0],
                "nodeIP": get_nodeIP(row[0]),#Aqui lo que tendriamos que hacer seria el consultaddbb para obtener la ip del nodo
                "neighborNodes": []
                }
                aux = row[0] # Establish the value of the auxiliar variable as the value of the new node
                node["neighborNodes"].append(row[1])
                if count_occurrences(rows, row[0]) == 1:
                    json.append(node)
            else:
                node["neighborNodes"].append(row[1])
                json.append(node)

        # Close the cursor and connection
        cur.close()
        db.close()
        # Convert the JSON data to a string
        # Return the JSON string
        return json
    except pymysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

@app.route('/overlay', methods=['GET'])
def get_connections():
    connections = get_Overlay()
    if connections is not None:
        return jsonify(connections)
    else:
        return "Error connecting to the database"

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
