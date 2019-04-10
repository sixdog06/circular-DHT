# python 3.7.1

import sys
import time
from socket import *
import threading
import os
import random
import numpy as np
import re

# send packets of file (UDP with ack)
def snd(file_clientSocket, receiver_id, event, sequence_number, ack_num, num_of_bytes, filedata):
	sender_message = ' '.join((event, str(sequence_number), str(ack_num), str(num_of_bytes)))
	sender_message = b'\r\n\r\n'.join((sender_message.encode(), filedata))
	file_clientSocket.sendto(sender_message, ('127.0.0.1', 50000 + receiver_id))

def write_responding_log(event, run_time, sequence_number, data_size, ack_num):
	responding_log = open('responding_log.txt', 'r+')
	responding_log.read()
	log = ' '.join((event, str(run_time), str(sequence_number), str(data_size), str(ack_num), '\n'))
	responding_log.write(log) 
	responding_log.close()

def write_requesting_log(event, run_time, sequence_number, data_size, ack_num):
	requesting_log = open('requesting_log.txt', 'r+')
	requesting_log.read()
	log = ' '.join((event, str(run_time), str(sequence_number), str(data_size), str(ack_num), '\n'))
	requesting_log.write(log) 
	requesting_log.close()

# receive the ping command (UDP)
def receive_ping_request():
	while True:
		predecessor_id, addr = serverSocket.recvfrom(1024)
		try:
			if predecessor_id and predecessor_id.decode().isdigit():
				serverSocket.sendto(str(own_id).encode(), addr)
				print(f'A ping request message was received from Peer {predecessor_id.decode()}.')
			else:
				f = open('received_file.pdf', 'rb+')
				f.read() #move the cursor to the end
				file_content = re.findall(b'.*\r\n\r\n([\d\D]*)', predecessor_id)[0]
				f.write(file_content)
				f.close()
				ack_num = int(predecessor_id.split()[1].decode()) + int(predecessor_id.split()[3].decode())
				ack_message = ' '.join(('ack', predecessor_id.split()[1].decode(), str(ack_num)))
				serverSocket.sendto(ack_message.encode(), addr)
				if predecessor_id.split()[0].decode() == 'fin_snd':
					print('The file is received.')

		except UnicodeDecodeError: # predecessor_id is the chunk of file
			f = open('received_file.pdf', 'wb+')
			file_content = re.findall(b'.*\r\n\r\n([\d\D]*)', predecessor_id)[0]
			f.write(file_content)
			f.close()

			ack_num = int(predecessor_id.split()[1].decode()) + int(predecessor_id.split()[3].decode())
			ack_message = ' '.join(('ack', predecessor_id.split()[1].decode(), str(ack_num)))
			serverSocket.sendto(ack_message.encode(), addr)

# receive the ping response (UDP)
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

# request a file (TCP)
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
	global sequence_number
	while True:
		try:
			connectionSocket, addr = TCP_serverSocket.accept()
			data = connectionSocket.recv(1024)		
			if data and not data.decode().split()[2] == 'start':
				predecessor_id = int(data.decode().split()[1])
				hash_value = int(data.decode().split()[2]) % 256 # hash function

				if (hash_value > predecessor_id and hash_value <= own_id) or (own_id < predecessor_id and hash_value > predecessor_id) or (own_id < predecessor_id and hash_value <= own_id):
					print(f'File {data.decode().split()[2]} is here.')
					print(f'A response message, destined for peer {int(data.decode().split()[0])}, has been sent.')
					print('We now start sending the file ………')
					
					TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
					TCP_clientSocket.connect(('127.0.0.1', 50000 + int(data.decode().split()[0])))
					reply = ' '.join((str(own_id), str(data.decode().split()[2]), 'start'))
					TCP_clientSocket.send(reply.encode())
					TCP_clientSocket.close()

					
					responding_log = open('responding_log.txt', 'w+') # create a file called responding_log.txt
					responding_log.close()
					f = open(data.decode().split()[2] + '.pdf', 'rb')
					filesize = len(f.read())
					f.close()
					
					# transfer the file
					try:
						with open(data.decode().split()[2] + '.pdf', 'rb') as f:
							file_clientSocket = socket(AF_INET, SOCK_DGRAM)
							file_clientSocket.settimeout(1) # timeout = 1s
							filedata = f.read(MSS)
							resend_flag = 0

							while filedata:
								while True:
									if f.tell() >= filesize: # whether is the last send, use ack_num to send sequence number
										snd(file_clientSocket, int(data.decode().split()[0]), 'fin_snd', sequence_number, 0, len(filedata), filedata)
									else:
										snd(file_clientSocket, int(data.decode().split()[0]), 'snd', sequence_number, 0, len(filedata), filedata)
									
									if resend_flag == 0:
										# write snd log
										write_responding_log('snd', round(time.time()-start_time, 2), sequence_number, len(filedata), 0)
									else:
										# write RTX log
										write_responding_log('RTX', round(time.time()-start_time, 2), sequence_number, len(filedata), 0)
										resend_flag = 0

									ack_message, (address, _) = file_clientSocket.recvfrom(1024)
									if ack_message:
										if ack_message.split()[0].decode() == 'ack':
											sequence_number = ack_message.split()[2].decode() # update sequence number
											write_responding_log('rcv', round(time.time()-start_time, 2), 0, len(filedata), sequence_number)
											break
									else:
										# write Drop log	
										write_responding_log('DROP', round(time.time()-start_time, 2), 0, len(filedata), 0)
										resend_flag = 1
								filedata = f.read(MSS)
							print('The file is sent.')
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
			elif data and data.decode().split()[2] == 'start':
				print('We now start receiving the file ………')
				print(f'Received a response message from peer {data.decode().split()[0]}, which has the file {data.decode().split()[1]}.')
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

# ping client (UDP)
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(3)

serverPort = 50000 + own_id
# ping server (UDP)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('127.0.0.1', serverPort))

# file message TCP server
TCP_serverSocket = socket(AF_INET, SOCK_STREAM)
TCP_serverSocket.bind(('127.0.0.1', serverPort))
TCP_serverSocket.listen(5)

# thread
thread_1 = threading.Thread(target=receive_ping_request)
thread_2 = threading.Thread(target=receive_ping_response)
thread_3 = threading.Thread(target=request_file)
thread_4 = threading.Thread(target=TCP_server)
thread_1.start()
thread_2.start()
thread_3.start()
thread_4.start()

time.sleep(3) # wait for initialization of the peers

# send the ping request every 10s
while True:
	clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + first_successive_id))
	clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + second_successive_id))
	time.sleep(10)

thread_4.join()
thread_3.join()
thread_2.join()
thread_1.join()