import pika
import os
import sys

def main():
    print('Ejecutamos el script')
    os.system("chmod -v +x setup_switch.sh")
    os.system("./setup_switch.sh" ) #lanzamos este comando para ejecutar el script de configuracion del switch
    # Establish a connection to RabbitMQ
    print('We have established a connetion with RabbitMQ')
    connection = pika.BlockingConnection(pika.ConnectionParameters('l2sm-overlay-manager-service'))
    channel = connection.channel()

    channel.exchange_declare(exchange='logs', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='logs', queue=queue_name)

    print(' [*] Waiting for logs. To exit press CTRL+C')

    # Define the callback function to handle incoming messages
    def callback(ch, method, properties, body):
        # Decode the message body from bytes to string
        message = body.decode('utf-8')

        execute_kubectl_command(message)
    # Start consuming messages from the queue
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True) #As the queue was defined as 'connections' we have to consume from that queue.
    # Keep consuming messages until the user interrupts the program
    
    channel.start_consuming()

    # Close the connection to RabbitMQ
    connection.close()
    

 #what does json.dumps(collected_messages) do?. This string can be used to store the list of messages in a file or send it over the network.
 #converts the collected_messages list to a JSON-formatted string

# This function checks if the given elements are present in the specified file.

def execute_kubectl_command(data):
    """
    We create a file in the directory /etc/l2sm with the name switchConfig.json and write the data to it in JSON format.
    Then we execute the kubectl command with the l2sm-vxlans plugin and the file path as an argument. 
    Finally, we empty the file to avoid errors in the next execution.
    """
    # Create a file path
    file_path = '/etc/l2sm/switchConfig.json' #We create the file in the /etc/l2sm directory with the name switchConfig.json
    os.system("./clear_vxlans.sh" )
    # Write the data to the file
    with open(file_path, 'w') as file:
        file.write(data[1:-1].replace('\\','')) #We write the data to the file in JSON format

    # Execute the kubectl command
    os.system('l2sm-vxlans --node_name=$NODENAME /etc/l2sm/switchConfig.json')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
