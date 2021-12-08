import mysql.connector
import os, time
import pika
from youtube_search import YoutubeSearch
from apiclient.discovery import build


print("start Music-Recommendation manager...")

api_key = 'AIzaSyBshgeUPe42QHm6BuS9ltjk03nc-gk9RpY'   	#Key de la api de youtube
youtube = build('youtube', 'v3', developerKey=api_key)	#Se construye el objeto de youtube

########### CONNEXIÓN A RABBIT MQ #######################

HOST = os.environ['RABBITMQ_HOST']
print("rabbit:"+HOST)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=HOST))
channel = connection.channel()

#El consumidor utiliza el exchange 'cartero'
channel.exchange_declare(exchange='cartero', exchange_type='topic', durable=True)

#Se crea un cola temporaria exclusiva para este consumidor (búzon de correos)
result = channel.queue_declare(queue="music", exclusive=True, durable=True)
queue_name = result.method.queue

#La cola se asigna a un 'exchange'
channel.queue_bind(exchange='cartero', queue=queue_name, routing_key="music")


##########################################################


########## ESPERA Y HACE ALGO CUANDO RECIBE UN MENSAJE ####

print(' [*] Waiting for messages. To exit press CTRL+C')

def callback(ch, method, properties, body):
	print(body.decode("UTF-8"))
	arguments = body.decode("UTF-8").split(" ")

	if (arguments[0]=="!music-r"):
		keys = ""
		for i in range(1, len(arguments)):
			keys = keys + arguments[i] + " "
		keys = keys + " Music"

		#print(keys)	#debugg

		results = youtube.search().list(q= keys, part = 'snippet', type='video', maxResults = 10)
		results = results.execute()
		result = "" 

		for i in range (5):
			result = result + results['items'][i]['snippet']['title']+ "\n"


		channel.basic_publish(exchange='cartero',routing_key="discord_writer",body=result)



channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()



#######################