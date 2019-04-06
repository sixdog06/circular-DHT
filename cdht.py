import sys
import time
from socket import *
from multiprocessing import Process
import os

# initialse the peer
if len(sys.argv) == 6 and float(sys.argv[5]) >=0 and float(sys.argv[5]) <=1:
	own_id = int(sys.argv[1])
	first_successive_id = int(sys.argv[2])
	second_successive_id = int(sys.argv[3])
	MSS = float(sys.argv[4])
	drop_probability = float(sys.argv[5])
else:
	print('please input the data of correct form')
	sys.exit()

# ping client
clientSocket = socket(AF_INET, SOCK_DGRAM)
'''
clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + first_successive_id))
time.sleep(0.5) # wait for 0.5 second
clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + second_successive_id))
'''
clientSocket.settimeout(3)

# ping server
serverPort = 50000 + own_id
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('127.0.0.1', serverPort))

while True:
	# send ping request to successive peers
	clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + first_successive_id))
	clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + second_successive_id))
	time.sleep(1)
	# receive the ping request
	predecessor_id, addr = serverSocket.recvfrom(1024)
	if predecessor_id:
		serverSocket.sendto(str(own_id).encode(), addr)
		print(f'A ping request message was received from Peer {predecessor_id.decode()}.')
	time.sleep(3)

	# receive the ping response
	try:
		data, (address, _) = clientSocket.recvfrom(1024)
		if data and int(data.decode()) == first_successive_id:
			print(f'A ping response message was received from Peer {first_successive_id}')
		elif data and int(data.decode()) == second_successive_id:
			print(f'A ping response message was received from Peer {second_successive_id}')	
	except OSError:
		pass		



