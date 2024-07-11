import json #en caso de que tengamos que cambiar el formado de datos de json a yaml
import logging
import pika
import pymysql
import yaml
from flask import Flask, abort, request
databaseIP = "database-service" #Podriamos poner "service_database"
# Create a Flask application
app = Flask(__name__)

# Define a route for the webhook endpoint
@app.route('/overlay', methods=['POST'])# This is the endpoint where the server is listening for incoming connections
def get_webhook():
    if request.method == 'POST':
        # Print the received data
        print("received data: ", request.yaml) #This is the data that the server receives from the client as a yaml object.
        received_data = create_json(load_yaml(request.yaml)) #We convert the yaml object to a dictionary and then to a json object.
        update_database(load_yaml(request.yaml)) #We update the database with the new connections.
        # Send the received data to the RabbitMQ server
        send_message(received_data) 
        return 'success', 200
    else:
        # If the request method is not POST, abort with a 400 error
        abort(400)

@app.route('/overlay', methods=['GET'])
def get_overlay():
    if request.method == 'GET':
        try:
            return jsonify(get_Connections())
        except Exception as e:
            logging.exception("An error ocurred whileprocessing the request")
            abort(500)
    else:
        # If the request method is not POST, abort with a 400 error
        abort(400)

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

# Function that receives a yaml file and transforms it into a directory for isier use.
# file_path: Ruta del archivo yaml a leer
def load_yaml(file_path):
    # Try to open the YAML file
    with open(file_path, 'r') as file:
        try:
            data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            print("Error loading YAML:", e)
    
    # Create a dictionary to store the result
    result_dict = {}
    
    # For each value of each key, split the string by '\n' and remove the last element to avoid an empty field
    for key, value in data['data'].items():
        if isinstance(value, str):
            result_dict[key] = value.split('\n')[:-1]
    for key, value in result_dict:
        if count_elements_in_table(key, value[4:]) == 0:
            result_dict[key] = value.split('\n')[:-1]
            
    return result_dict

# Function that collects a dictionary and formats it into a JSON object.
def create_json(data):
    json_data = []
    for key, value in data.items():
        node = {
            "name": key,
            "nodeIP": get_nodeIP(key),#Aqui lo que tendriamos que hacer seria el consultaddbb para obtener la ip del nodo            
            "neighborNodes": []
        }
        for neighbor in value:
            if count_elements_in_table(key,value) == 0: #We check if the node already has a connection with the neighbor node.
                #If the value is 0, it means that the node does not have a connection with the neighbor node.
                node["neighborNodes"].append(neighbor[4:])
        json_data.append(node)

    return json_data
    # Loop through each node in the JSON data


def count_elements_in_table(node1, node2):#This function is used to check if a node already has a connection with another node.
    #Count the number of elements in a table that match a given list of values.
    try:
        # Connect to the MySQL database
        db = pymysql.connect(host=databaseIP,user="l2sm",password="l2sm;",db="L2SM")
        
        # Create a cursor object to execute SQL queries
        cur = db.cursor()
        #CREATE TABLES IF THEY DO NOT EXIST
        connections = "CREATE TABLE IF NOT EXISTS connections (node TEXT NOT NULL, connection TEXT NOT NULL);"
        #We create a table called connections with two columns: node and connection.
        #Node is the node that has created the connection
        #Connection is the node that has been connected to.

        cur.execute(connections) #We execute the query to create the table.
        db.commit()#We commit the changes to the database.

        # Construct the SQL query to count the elements in the table
        query = "SELECT COUNT(*) FROM connections WHERE node = %s AND connection = %s"
        
        # Execute the SQL query with the elements as parameters
        cur.execute(query, node1, node2)
        
        # Fetch the result of the query
        count = cur.fetchone()[0]
        
        # Close the cursor and connection
        cur.close()
        db.close()
        
        return count
    except pymysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def update_database(data):#This function is used to check if a node already has a connection with another node.
    #Count the number of elements in a table that match a given list of values.
    try:
        # Connect to the MySQL database
        db = pymysql.connect(host=databaseIP,user="l2sm",password="l2sm;",db="L2SM")
        # Create a cursor object to execute SQL queries
        cur = db.cursor()

        #CREATE TABLES IF THEY DO NOT EXIST
        connections = "CREATE TABLE IF NOT EXISTS connections (node TEXT NOT NULL, connection TEXT NOT NULL);"
        cur.execute(connections) #We execute the query to create the table.
        

        # Construct the SQL query to count the elements in the table
        query = "INSERT INTO connections(node, connection) VALUES(%s,%s)"
        for key, value in data.items():
            for v in value:
                cur.execute(query, key, v[4:0])# Execute the SQL query with the elements as parameters
        
        db.commit()#We commit the changes to the database.

        # Close the cursor and connection
        cur.close()
        db.close()

    except pymysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def send_message(message):
  """
  This function adds a command to the RabbitMQ server.

  It establishes a connection to the RabbitMQ server using pika library,
  creates a channel, and declares a queue to send messages to.

  Note: The commented line is an example of how to publish a message to the queue.
  """
  # Informacion sobre rabbitmq obtenida de https://www.rabbitmq.com/tutorials/tutorial-one-python
  #We establish a connection to the RabbitMQ server using pika library
  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()
  #We create a channel called connections to send the messages to.
  channel.queue_declare(queue='connections') #Notice that we have called the queue connections, all the devices will have to connec to this queue to receive the messages.

  # Convert message to JSON
  #json_message = json.dumps(message) #We convert the message to a json object.

  channel.basic_publish(exchange='',#The exchange is the name of the exchange where the message is going to be sent.
                          routing_key='connections', #The routing key is the name of the queue where the message is going to be sent.
                          body=message) #The body is the message that is going to be sent.
  
  print("Message sent:", message)

  connection.close()

def count_occurrences(rows, value):
    count = 0
    for row in rows:
        if row[0] == value:
            count += 1
    return count

def get_Connections():#This function is used to check if a node already has a connection with another node.
    #Count the number of elements in a table that match a given list of values.
    print('Hemos llamado a la funcion get_conections()')
    try:
        # Connect to the MySQL database
        db = pymysql.connect(host=databaseIP,user="l2sm",password="l2sm;",db="L2SM")
        print('nos conectamos con la base de datos')
        # Create a cursor object to execute SQL queries
        cur = db.cursor()
        #CREATE TABLES IF THEY DO NOT EXIST
        connections = "CREATE TABLE IF NOT EXISTS connections (node TEXT NOT NULL, connection TEXT NOT NULL);"
        #We create a table called connections with two columns: node and connection.
        print("creamos la tabla")
        cur.execute(connections) #We execute the query to create the table.
        db.commit()#We commit the changes to the database.

        #Execute the query requesting all the values in the table connections.
        cur.execute("SELECT node, connection FROM connections")
        print("ejecutamos la query")

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
                "neighborNodes": []
                }
                aux = row[0] # Establish the value of the auxiliar variable as the value of the new node
                node["neighborNodes"].append(row[1])
            else:
                node["neighborNodes"].append(row[1])
                json.append(node)

        # Close the cursor and connection
        print("cerramos la conexion")
        cur.close()
        db.close()

        # Return the JSON string
        return json

    except pymysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

"""
  channel.basic_publish(exchange='',
        routing_key='',
        body='Hello World!')
  """

'''
# Example usage
file_path = 'general-configMap.yaml'
data = load_yaml(file_path)
python3: can't open file '/home/ahermosilla/L2S-M/l2sm-overlay-manager.py': [Errno 2] No such file or directory
print(data)
'''

# Run the application if this file is executed directly
if __name__ == '__main__':
  # Start the Flask application
  app.run(host='0.0.0.0', port=80) #The 0.0.0.0 means it is listening on all the interfaces of the machine.
  #This is the port where the server is listening for incoming connections.
