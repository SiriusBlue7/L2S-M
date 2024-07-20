from flask import Flask, jsonify, request
import pymysql
import pika
import yaml
import json
app = Flask(__name__)
databaseIP = "l2sm-database-service" #This is the IP of the database service. We have to change it to the correct IP of the database service.

def get_nodeIP(node):
    """
    This function is used to get the IP address of a node from the database.
    
    It queries the switches table in the database and returns the IP address of the node.
    """
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

def count_occurrences(rows, value):
    count = 0
    for row in rows:
        if row[0] == value:
            count += 1
    return count


def get_Overlay():#This function is used to check if a node already has a connection with another node.
    #Count the number of elements in a table that match a given list of values.
    try:
        # Connect to the MySQL database
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



def load_yaml(data):
    """
    This function is used to load a YAML file and convert it into a dictionary.

    Once the dictionary is created, we check some conditions to make sure the data is correct.
    The commands in each of the elements of the dictionary are checked to see if they are to be added or deleted.
    If the command is to be added, we check if the connection is already in the database.
    If the command is to be deleted, we check if the connection is in the database.
    """
    
    # Create a dictionary to store the result
    dict = {}
    
    # For each value of each key, split the string by '\n' and remove the last element to avoid an empty field
    for key, value in data['data'].items():
        print(value)
        if isinstance(value, str):
            dict[key] = value.split('\n')[:-1]
    #We have created a dictionary with the connections to be created or deleted.

    for key, value in dict.items():
        print(key)
        for v in value:
            if v[:3] == 'add' and count_elements_in_table(key,v[4:]) == 0 : #We check if the value is to be added to the table in the database.
                #We make sure the element is to be added to the table in the database and also if the element is not already in the table.

                #We call the function to update the database, with the argument 'add' to delete the connection.
                #The function will receive the command del and will send the query to delete the connection between the two nodes.
                print(f"We add a connection between {key} and {v[4:]} in the database")
                update_database('add', key, v[4:]) #We update the database with the new connection.
                pass
            elif v[:3] == 'del' and count_elements_in_table(key,v[4:]) == 1 : #We check if the value is to be deleted from the table in the database.
                #We make sure the element is to be deleted from the table in the database and also if the element is already in the table.
                
                #We call the function to update the database, with the argument 'del' to delete the connection.
                #The function will receive the command del and will send the query to delete the connection between the two nodes.
                print(f"We remove a connection between {key} and {v[4:]} in the database")
                update_database('del', key, v[4:]) #We update the database by deleting the connection.
                pass
        print(f"-----End of modifications for node{key}--------------------")
    return dict


def count_elements_in_table(node1, node2):
    """
    This function is used to count the number of connections between two nodes in the database.

    It counts the elements in the connections table that match the given node1 and node2 values.
    """
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
        cur.execute(query,(node1, node2))
        
        # Fetch the result of the query
        count = cur.fetchone()[0]
        
        # Close the cursor and connection
        cur.close()
        db.close()
        
        return count
    except pymysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def update_database(command, node1, node2):
    """
    This function is used to add or delete a connection between two nodes in the database.

    Add: Add a connection between two nodes to the connections table.
    Del: Delete a connection between two nodes from the connections table.
    """
    try:
        # Connect to the MySQL database
        db = pymysql.connect(host=databaseIP,user="l2sm",password="l2sm;",db="L2SM")
        # Create a cursor object to execute SQL queries
        cur = db.cursor()

        #CREATE TABLES IF THEY DO NOT EXIST
        connections = "CREATE TABLE IF NOT EXISTS connections (node TEXT NOT NULL, connection TEXT NOT NULL);"
        cur.execute(connections) #We execute the query to create the table.
        
        if command == 'add':
            query = "INSERT INTO connections(node, connection) VALUES(%s,%s)"
            cur.execute(query, (node1, node2))
        elif command == 'del':
            query = "DELETE FROM connections WHERE node = %s AND connection = %s"
            cur.execute(query, (node1, node2))
        
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
  
  #We declare the exchange where the message is going to be sent.
    #The fanout exchange broadcasts all the messages it receives to all the queues it knows.
  channel.exchange_declare(exchange='logs', exchange_type='fanout') 

  # Convert message to JSON
  #json_message = json.dumps(message) #We convert the message to a json object.

  channel.basic_publish(exchange='logs',#The exchange is the name of the exchange where the message is going to be sent.
                          routing_key='', #The routing key is the name of the queue where the message is going to be sent. As this broadcast it will be to all the queues.
                          body=json.dumps(message)) #The body is the message that is going to be sent.
  
  print("Message sent:", message)

  connection.close()


@app.route('/connections', methods=['GET'])
def get_connections():
    connections = get_Overlay()
    if connections is not None:
        return jsonify(connections)
    else:
        return "Error connecting to the database"

@app.route('/overlay', methods=['POST'])
def add_connections():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
        # Check if the file has a .yaml extension

    if file.filename.endswith('.yaml'):
        # Code to handle .yaml file
        try:
            file_content = file.read().decode('utf-8')  # Read the file content and decode it to a string
            print("Estamos imprimiendo el contenido del archivo yaml")
            data = yaml.safe_load(file_content)  # We load the yaml from the string
            print("Almacenamos el contenido del fichero en un dicccionario")
            load_yaml(data)  # We process the yaml data. We add the connections to the database.
            #We process the file and update the database with the modifications requested in the file.            
            print(get_Overlay())
            send_message(json.dumps(get_Overlay()))
            #we send a message to the queue connections with the json created from the database.
            
            return 'File uploaded and processed successfully'
        except yaml.YAMLError as e:
            return f'Error parsing YAML: {str(e)}', 400
    else:
        return 'Invalid file format. Only .yaml files are allowed', 400


if __name__ == '__main__':
    app.run('0.0.0.0', port=8080, debug=True, use_debugger=False, use_reloader=False)

