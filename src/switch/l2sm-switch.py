import pika
import json
import subprocess
import os
import sys

def main():
    os.system("./setup_switch.sh" ) #lanzamos este comando para ejecutar el script de configuracion del switch
    # Establish a connection to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('overlay_manager_service'))
    channel = connection.channel()

    # Declare the queue to consume messages from
    channel.queue_declare(queue='connections')

    # Create a list to store the collected messages
    collected_messages = callback()

    # Define the callback function to handle incoming messages
    def callback(ch, method, properties, body):
        # Decode the message body from bytes to string
        message = body.decode('utf-8')
        
        if check_ip_address(message,get_IPaddress('eth0')) == True:
            check_elements_in_file('/var/connections.txt', get_neighbor_nodes(message, get_IPaddress('eth0')))
            execute_kubectl_command(message)
        else :
            print("this message is not for this switch")
    # Start consuming messages from the queue
    channel.basic_consume(queue='connections', on_message_callback=callback, auto_ack=True) #As the queue was defined as 'connections' we have to consume from that queue.
    # Keep consuming messages until the user interrupts the program
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        pass

    # Close the connection to RabbitMQ
    connection.close()
    
    # Convert the collected_messages list to JSON and return it
    return json.dumps(collected_messages)

 #what does json.dumps(collected_messages) do?. This string can be used to store the list of messages in a file or send it over the network.
 #converts the collected_messages list to a JSON-formatted string

# The function runs the 'ip a s' command to get the IP address of a network interface. It then parses the output of the command to find the IP address and returns it as a string.
def get_IPaddress(interface):
    # Run the 'ip a s' command and capture the output
    result = subprocess.run(['ip', 'a', 's', interface], capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0:
        # Parse the output to find the IP address
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if 'inet' in line:
                ip_address = line.split()[1].split('/')[0]
                return ip_address
    else:
        # Handle the case when the command fails
        print(f"Failed to get IP address for interface {interface}")
        return None
'''
# Example usage
interface = 'eth0'
ip_address = get_IPaddress(interface)
print(f"IP address of {interface}: {ip_address}")
'''

'''
json_example = [
    {
        "name": "l2sm1",
        "nodeIP": "10.1.14.58",
        "neighborNodes": ["l2sm2"]
    },
    {
        "name": "l2sm2",
        "nodeIP": "10.1.72.111",
        "neighborNodes": ["l2sm1"]
    }
]
'''

def check_ip_address(json_data, ip_address):
    for element in json_data:
        if element['nodeIP'] == ip_address:
            return True
    return False

'''
# Example usage
ip_address_to_check = '10.1.14.58'
result = check_ip_address(json_example, ip_address_to_check)
print(f"IP address {ip_address_to_check} found in json_example: {result}")
'''


# This function takes a JSON data and an IP address as input and returns the neighbor nodes associated with the given IP address.
def get_neighbor_nodes(json_data, ip_address):
    neighbor_nodes = []
    for element in json_data:
        if element['nodeIP'] == ip_address:
            neighbor_nodes = element['neighborNodes']
            break
    return neighbor_nodes
'''
# Example usage
json_data = [
    {
        "name": "l2sm1",
        "nodeIP": "10.1.14.58",
        "neighborNodes": ["l2sm2"]
    },
    {
        "name": "l2sm2",
        "nodeIP": "10.1.72.111",
        "neighborNodes": ["l2sm1"]
    }
]
ip_address = '10.1.14.58'
result = get_neighbor_nodes(json_data, ip_address)
print(f"Neighbor nodes of {ip_address}: {result}")
'''

# This function checks if the given elements are present in the specified file.
def check_elements_in_file(file_path, elements):
    #Habria que crear  una comprobacion para ver si el fichero existe o no, haciendolo con un if 
    # Check if the file exists
    if os.path.exists(file_path):
        # Open the file in read mode
        with open(file_path, 'r') as file:
            # Read the content of the file
            file_content = file.read()
            # Iterate over each element
            for element in elements:
                # Check if the element is present in the file content
                if element in file_content:
                    print(f"{element} is present in the file.")
                else:
                    print(f"{element} is not present in the file.")
                    # Add the missing element to the file
                    with open(file_path, 'a') as file:
                        file.write(f"\n{element}")
    else:
        print(f"File '{file_path}' not found. We will create it.")
        # Create an empty file with the specified file path
        with open(file_path, 'w') as file:
            # Write the elements to the file
            file.write('\n'.join(elements))
        print(f"File '{file_path}' created with the elements.")
'''
# Example usage
file_path = 'text.txt'
elements = ['apple', 'banana', 'orange']
check_elements_in_file(file_path, elements)
'''

def execute_kubectl_command(data):#tenemos que guardar el fichero en la carpeta y despues ejecutamos ese fichero
    # Create a file path
    file_path = '/etc/l2sm/switchConfig.json' #We create the file in the /etc/l2sm directory with the name switchConfig.json

    # Write the data to the file
    with open(file_path, 'w') as file:
        file.write(json.dumps(data)) #We write the data to the file in JSON format

    # Execute the kubectl command
    os.system(f'l2sm-vxlans --node_name=$NODENAME {file_path}')
    
    # Empty the file
    with open(file_path, 'w') as file:
        file.write('') #We empty the file after executing the kubectl command to avoid errors in the next execution

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
