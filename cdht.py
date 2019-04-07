# python 3.7.1

import sys
import time
from socket import *
import threading
import os
import random

# send event
def snd(receiver_index, index, num_of_bytes, ack_number, filedata, filesize):
	sender_message = ' '.join(('snd', str(round(time.time() - start_time, 2)), str(sequence_number), str(num_of_bytes), str(ack_number)))
	log = sender_message
	if index*num_of_bytes < filesize:
		filesize = (index * num_of_bytes + num_of_bytes)
	sender_message = b' '.join((sender_message.encode(), filedata))
	clientSocket.sendto(sender_message, ('127.0.0.1', 50000 + int(receiver_index)))
	print(log)
	return log

# receive event
def rcv(receiver_index, num_of_bytes, ack_number, filedata):
	sender_message = ' '.join(('rcv', str(time.time() - start_time), '0', str(ack_number), str(ack_number)))
	log = sender_message
	sender_message = sender_message.encode()
	clientSocket.sendto(sender_message, ('127.0.0.1', 50000 + receiver_index))
	return log

# receive the ping command
def receive_ping_request():
	while True:
		predecessor_id, addr = serverSocket.recvfrom(1024)
		if predecessor_id and predecessor_id.decode().isdigit():
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
				print(f'File request message for {filename} has been sent to my successor.')
				# file client
				TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
				TCP_clientSocket.connect(('127.0.0.1', 50000 + first_successive_id))
				file_request = ' '.join((str(own_id), str(own_id), str(filename)))
				TCP_clientSocket.send(file_request.encode())
				TCP_clientSocket.close()

# TCP server to get the file request
def TCP_server():
	while True:
		try:
			connectionSocket, addr = TCP_serverSocket.accept()
			data = connectionSocket.recv(1024)			
			if data:
				predecessor_id = int(data.decode().split()[1])
				hash_value = int(data.decode().split()[2]) % 256 # hash function

				if (hash_value > predecessor_id and hash_value <= own_id) or (own_id < predecessor_id and hash_value > predecessor_id) or (own_id < predecessor_id and hash_value <= own_id):
					print(f'File {hash_value} is here.')
					print(f'A response message, destined for peer {int(data.decode().split()[0])}, has been sent.')
					print('We now start sending the file ………')
					
					# file sender
					try:
						with open(data.decode().split()[2] + '.pdf', 'rb') as f:
							filedata = f.read(300)
							file_clientSocket = socket(AF_INET, SOCK_DGRAM)
							file_clientSocket.settimeout(1) # timeout = 1s

							num_of_chunk = len(filedata) / MSS
							for i in range(round(num_of_chunk)):
								snd(int(data.decode().split()[0]), i, MSS, 0, filedata, len(filedata))
								#data, (address, _) = clientSocket.recvfrom(1024)
							# send the remain part of file
								if len(filedata) % MSS:						
									snd(int(data.decode().split()[0]), num_of_chunk * MSS, MSS, 0, filedata, len(filedata))
							file_clientSocket.close()
					except IOError:
						pass
					

				else:
					print(f'File {data.decode().split()[2]} is not stored here.')
					TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
					TCP_clientSocket.connect(('127.0.0.1', 50000 + first_successive_id))
					file_request = str(int(data.decode().split()[0])) + ' ' + str(own_id) + ' ' + str(int(data.decode().split()[2]))
					TCP_clientSocket.send(data)
					TCP_clientSocket.close()
					print('File request message has been forwarded to my successor.')	
		except IOError:
			pass


start_time = time.time()
# initialse the peer
if len(sys.argv) == 6 and float(sys.argv[5]) >=0 and float(sys.argv[5]) <=1:
	own_id = int(sys.argv[1])
	first_successive_id = int(sys.argv[2])
	second_successive_id = int(sys.argv[3])
	MSS = int(sys.argv[4])
	drop_probability = float(sys.argv[5])
else:
	print('please input the data of correct form')
	sys.exit()

sequence_number = 1 # file transfer sequence number

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