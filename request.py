import sys
import requests

def perform_get_request(ip, port):
    # Perform GET request logic here
    print("GET request")
    url = f"http://{ip}:{port}/connections"
    print(f"URL: {url}")
    response = requests.get(url)
    print(response.text)

# Define a function to perform a POST request
def perform_post_request(ip, port):
    # Specify the URL for the request
    print("POST request")
    
    url = f"http://{ip}:{port}/overlay"
    
    # Prepare the file to be sent in the request
    files = {'file': open('overlay.yaml', 'rb')}
    # Print the URL we are going to send the request to
    print(f"URL: {url}")
    # Send the POST request with the specified URL and file
    response = requests.post(url, files=files)
    
    # Print the response text
    print(response.text)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python Requests.py <request_type> <ip_address> <port>")
        sys.exit(1)

    request_type = sys.argv[1]
    ip_address = sys.argv[2]
    port = sys.argv[3]

    if request_type.lower() == "get":
        perform_get_request(ip_address, port)
    elif request_type.lower() == "post":
        perform_post_request(ip_address, port)
    else:
        print("Invalid request type. Please specify either 'get' or 'post'.")
        sys.exit(1)
