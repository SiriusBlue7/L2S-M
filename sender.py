#!/usr/bin/env python
import pika
import sys

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='10.152.183.227'))
channel = connection.channel()

channel.exchange_declare(exchange='logs', exchange_type='fanout')

message = '[{"name":"tfg-ahermosilla-3","neighborNodes":["tfg-ahermosilla-2"],"nodeIP":"10.1.169.122"},{"name":"tfg-ahermosilla-2","neighborNodes":["tfg-ahermosilla-3"],"nodeIP":"10.1.53.198"}]'
channel.basic_publish(exchange='logs', routing_key='', body=message)
print(f" [x] Sent {message}")
connection.close()
