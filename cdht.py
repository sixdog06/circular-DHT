# python 3.7.1

import sys
import time
from socket import *
import threading
import os

# receive the ping command
def receive_ping_request():
	while True:
		predecessor_id, addr = serverSocket.recvfrom(1024)
		if predecessor_id:
			serverSocket.sendto(str(own_id).encode(), addr)
			print(f'A ping request message was received from Peer {predecessor_id.decode()}.')

# receive the ping response
def receive_ping_response():
	while True:
		try:
			data, (address, _) = clientSocket.recvfrom(1024)
			if data and int(data.decode()) == first_successive_id:
				print(f'A ping response message was received from Peer {first_successive_id}')
			elif data and int(data.decode()) == second_successive_id:
				print(f'A ping response message was received from Peer {second_successive_id}')	
		except OSError:
			pass

# request a file
def request_file():
	while True:
		command = input()
		command = command.split()
		if len(command) == 2 and command[0] == 'request' and command[1].isdigit():
			filename = int(command[1])
			if filename >= 0 and filename < 10000:
				hash_value = filename % 256 # hash function
				print(f'File request message for {filename} has been sent to my successor.')
				# file client
				TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
				TCP_clientSocket.connect(('127.0.0.1', 50000 + first_successive_id))
				file_request = str(own_id) + ' ' + str(own_id) + ' ' + str(hash_value)
				TCP_clientSocket.send(file_request.encode())
				TCP_clientSocket.close()

def TCP_server():
	while True:
		try:
			connectionSocket, addr = TCP_serverSocket.accept()
			data = connectionSocket.recv(1024)			
			if data:
				predecessor_id = int(data.decode().split()[1])
				hash_value = int(data.decode().split()[2]) % 256

				if (hash_value > predecessor_id and hash_value <= own_id) or (own_id < predecessor_id and hash_value > predecessor_id) or (own_id < predecessor_id and hash_value <= own_id):
					print('it is', hash_value)
				else:
					TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
					TCP_clientSocket.connect(('127.0.0.1', 50000 + first_successive_id))
					file_request = str(int(data.decode().split()[0])) + ' ' + str(own_id) + ' ' + str(int(data.decode().split()[2]))
					TCP_clientSocket.send(data)
					TCP_clientSocket.close()					
		except IOError:
			pass

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
clientSocket.settimeout(3)

serverPort = 50000 + own_id
# ping server
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('127.0.0.1', serverPort))

# file server
TCP_serverSocket = socket(AF_INET, SOCK_STREAM)
TCP_serverSocket.bind(('127.0.0.1', serverPort))
TCP_serverSocket.listen(5)

'''
# file client
TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
TCP_clientSocket.connect(('127.0.0.1', serverPort))
'''

# define the thread
thread_1 = threading.Thread(target=receive_ping_request)
thread_2 = threading.Thread(target=receive_ping_response)
thread_3 = threading.Thread(target=request_file)
thread_4 = threading.Thread(target=TCP_server)
thread_1.start()
thread_2.start()
thread_3.start()
thread_4.start()

time.sleep(3) # wait for initialization of the peers

# send the ping request
while True:
	clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + first_successive_id))
	clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + second_successive_id))
	time.sleep(10)

thread_4.join()
thread_3.join()
thread_2.join()
thread_1.join()