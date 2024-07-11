import pika
import json
#!/usr/bin/env python

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('10.1.169.112'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(f" [x] Received {body.decode()}")
        json_received = json.loads(body.decode())
        print(json_received)
        with open('swtichConfig.json','w') as file:
            file.write(body.decode())

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
