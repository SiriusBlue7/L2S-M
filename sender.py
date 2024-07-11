import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('10.1.169.112'))
channel = connection.channel()

channel.queue_declare(queue='hello')
message=('[{"name":"tfg-ahermosilla-3","neighborNodes":["tfg-ahermosilla-2"],"nodeIP":"10.1.169.122"},{"name":"tfg-ahermosilla-2","neighborNodes":["tfg-ahermosilla-3"],"nodeIP":"10.1.53.198"}]')
channel.basic_publish(exchange='', routing_key='hello', body=message)
print(" [x] Sent message  ")
connection.close()
