# python 3.7.1

import sys
import time
from socket import *
import threading
import os
import random
import numpy as np
import re
300       	
# send packets of file (UDP with ack)
def snd(file_clientSocket, receiver_id, event, sequence_number, ack_num, num_of_bytes, filedata):
	sender_message = ' '.join((event, str(sequence_number), str(ack_num), str(num_of_bytes)))
	sender_message = b'\r\n\r\n'.join((sender_message.encode(), filedata))
	file_clientSocket.sendto(sender_message, ('127.0.0.1', 50000 + receiver_id))

def write_responding_log(event, run_time, sequence_number, data_size, ack_num):
	responding_log = open('responding_log.txt', 'r+')
	responding_log.read()
	log = f'{event:16}{str(run_time):16}{str(sequence_number):16}{str(data_size):16}{str(ack_num)}\n'
	responding_log.write(log) 
	responding_log.close()

def write_requesting_log(event, run_time, sequence_number, data_size, ack_num):
	requesting_log = open('requesting_log.txt', 'r+')
	requesting_log.read()
	log = f'{event:16}{str(run_time):16}{str(sequence_number):16}{str(data_size):16}{str(ack_num)}\n'
	requesting_log.write(log) 
	requesting_log.close()

# receive the ping command or file(UDP)
def receive_ping_request():
	global predecessor_id
	while True:
		receive_message, addr = serverSocket.recvfrom(1024)
		try:
			if receive_message and receive_message.decode().split()[0] == 'first_successive_id' or receive_message.decode().split()[0] == 'second_successive_id':
				serverSocket.sendto((str(own_id) + ' ' + receive_message.decode().split()[2]).encode(), addr)
				pid = int(receive_message.decode().split()[1])
				if not pid in predecessor_id:
					if receive_message.decode().split()[0] == 'first_successive_id':
						predecessor_id[0] = pid
					elif receive_message.decode().split()[0] == 'second_successive_id':
						predecessor_id[1] = pid				
				print(f'A ping request message was received from Peer {receive_message.decode().split()[1]}.')
			else:
				f = open('received_file.pdf', 'rb+')
				f.read() # move the cursor to the end
				file_content = re.findall(b'.*\r\n\r\n([\d\D]*)', receive_message)[0]
				f.write(file_content)
				f.close()
				write_requesting_log('rcv', round(time.time()-start_time, 2), int(receive_message.split()[1].decode()), int(receive_message.split()[3].decode()), 0)
				
				ack_num = int(receive_message.split()[1].decode()) + int(receive_message.split()[3].decode())
				ack_message = ' '.join(('ack', receive_message.split()[1].decode(), str(ack_num)))
				serverSocket.sendto(ack_message.encode(), addr)
				write_requesting_log('snd', round(time.time()-start_time, 2), 0, int(receive_message.split()[3].decode()), ack_num)
				if receive_message.split()[0].decode() == 'fin_snd':
					print('The file is received.')

		except UnicodeDecodeError: # receive_message is the chunk of file
			responding_log = open('requesting_log.txt', 'w+') # create a file called responding_log.txt
			responding_log.close()
			
			f = open('received_file.pdf', 'wb+')
			file_content = re.findall(b'.*\r\n\r\n([\d\D]*)', receive_message)[0]
			f.write(file_content)
			f.close()
			write_requesting_log('rcv', round(time.time()-start_time, 2), int(receive_message.split()[1].decode()), int(receive_message.split()[3].decode()), 0)

			ack_num = int(receive_message.split()[1].decode()) + int(receive_message.split()[3].decode())
			ack_message = ' '.join(('ack', receive_message.split()[1].decode(), str(ack_num)))
			serverSocket.sendto(ack_message.encode(), addr)
			write_requesting_log('snd', round(time.time()-start_time, 2), 0, int(receive_message.split()[3].decode()), ack_num)

# receive the ping response (UDP)
def receive_ping_response_first():
	global first_alive_flag
	global first_successive_id
	try:
		data, (address, _) = clientSocket_first.recvfrom(1024)
		if data and int(data.decode().split()[0]) == first_successive_id:
			print(f'A ping response message was received from Peer {first_successive_id}')
			first_alive_flag = 0
		print(data.decode().split()[1])
	except OSError:
		first_alive_flag += 1
		if first_alive_flag >= 2:
			print('safaef')

def receive_ping_response_second():
	global second_alive_flag
	global second_successive_id
	try:
		data, (address, _) = clientSocket_second.recvfrom(1024)
		if data and int(data.decode().split()[0]) == second_successive_id:
			print(f'A ping response message was received from Peer {second_successive_id}')
			second_alive_flag = 0
		print(data.decode().split()[1])
	except OSError:
		second_alive_flag += 1
		if second_alive_flag >= 2:
			print('!!!!!')

# request a file (TCP)
def request_file():
	global predecessor_id
	global work_flag
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
		elif command and command[0] == 'quit':
			TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
			TCP_clientSocket.connect(('127.0.0.1', 50000 + predecessor_id[0]))
			quit_message = ' '.join((str(first_successive_id), str(second_successive_id), 'quit'))
			TCP_clientSocket.send(quit_message.encode())				
			TCP_clientSocket.close()

			TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
			TCP_clientSocket.connect(('127.0.0.1', 50000 + predecessor_id[1]))
			quit_message = ' '.join((str(predecessor_id[0]), str(first_successive_id), 'quit'))
			TCP_clientSocket.send(quit_message.encode())				
			TCP_clientSocket.close()
			print(f'Peer {own_id} will depart from the network.')
			work_flag = 0

# TCP server to get the file request
def TCP_server():
	global sequence_number
	global first_successive_id
	global second_successive_id
	while True:
		try:
			connectionSocket, addr = TCP_serverSocket.accept()
			data = connectionSocket.recv(1024)
			# start: know which peer has the file and start to receive, quit: departure of a peer
			if data and not data.decode().split()[2] == 'start' and not data.decode().split()[2] == 'quit':
				receive_message = int(data.decode().split()[1])
				hash_value = int(data.decode().split()[2]) % 256 # hash function

				if (hash_value > receive_message and hash_value <= own_id) or (own_id < receive_message and hash_value > receive_message) or (own_id < receive_message and hash_value <= own_id):
					print(f'File {data.decode().split()[2]} is here.')
					print(f'A response message, destined for peer {int(data.decode().split()[0])}, has been sent.')
					print('We now start sending the file ………')
					
					# let receiver know that sender is found
					TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
					TCP_clientSocket.connect(('127.0.0.1', 50000 + int(data.decode().split()[0])))
					reply = ' '.join((str(own_id), str(data.decode().split()[2]), 'start'))
					TCP_clientSocket.send(reply.encode())
					TCP_clientSocket.close()

					# create a log file called responding_log.txt
					responding_log = open('responding_log.txt', 'w+')
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
							drop_resend_flag = 0

							while filedata:
								while True:
									if random.random() > drop_probability:
										if f.tell() >= filesize: # whether is the last send, use ack_num to send sequence number
											snd(file_clientSocket, int(data.decode().split()[0]), 'fin_snd', sequence_number, 0, len(filedata), filedata)
										else:
											snd(file_clientSocket, int(data.decode().split()[0]), 'snd', sequence_number, 0, len(filedata), filedata)
										# write log
										if resend_flag == 0:
											# write snd log
											write_responding_log('snd', round(time.time()-start_time, 2), sequence_number, len(filedata), 0)

									try:
										ack_message, (address, _) = file_clientSocket.recvfrom(1024)				
										if ack_message:
											if ack_message.split()[0].decode() == 'ack':
												if resend_flag == 1:
													write_responding_log('RTX', round(time.time()-start_time, 2), sequence_number, len(filedata), 0)
												sequence_number = ack_message.split()[2].decode() # update sequence number		
												write_responding_log('rcv', round(time.time()-start_time, 2), 0, len(filedata), sequence_number)
												resend_flag = 0
												break
									except IOError: # timeout happens
										if resend_flag == 1:
											write_responding_log('RTX/Drop', round(time.time()-start_time, 2), sequence_number, len(filedata), 0)
										else:
											write_responding_log('DROP', round(time.time()-start_time, 2), sequence_number, len(filedata), 0)
											resend_flag = 1
								filedata = f.read(MSS)
							print('The file is sent.')
							file_clientSocket.close()
					except IOError: # if no file in this peer for correct name, do nothing
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
				print(f'Received a response message from peer {data.decode().split()[0]}, which has the file {data.decode().split()[1]}.')
				print('We now start receiving the file ………')
			elif data and data.decode().split()[2] == 'quit':
				first_successive_id = int(data.decode().split()[0])
				second_successive_id = int(data.decode().split()[1])
				print(f'My first successor is now peer {first_successive_id}.')
				print(f'My second successor is now peer {second_successive_id}.')
		except IOError:
			pass

# record the start time of the program
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

predecessor_id = ['#', '#']
sequence_number = 1 # file transfer sequence number
work_flag = 1
ping_seq = 0
first_alive_flag = 0
second_alive_flag = 0

# ping client (UDP)
clientSocket_first = socket(AF_INET, SOCK_DGRAM)
clientSocket_first.settimeout(2)

clientSocket_second = socket(AF_INET, SOCK_DGRAM)
clientSocket_second.settimeout(2)

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
thread_4 = threading.Thread(target=request_file)
thread_5 = threading.Thread(target=TCP_server)

thread_1.start()
thread_4.start()
thread_5.start()

time.sleep(3) # wait for initialization of the peers

# send the ping request every 10s
while True:
	# work_flag(0: already depart)
	if work_flag == 1:
		m_1 = ' '.join(('first_successive_id', str(own_id), str(ping_seq)))
		m_2 = ' '.join(('second_successive_id', str(own_id), str(ping_seq)))
		clientSocket_first.sendto(m_1.encode(), ('127.0.0.1', 50000 + first_successive_id))
		receive_ping_response_first()
		clientSocket_second.sendto(m_2.encode(), ('127.0.0.1', 50000 + second_successive_id))
		receive_ping_response_second()
		ping_seq += 1
		time.sleep(10)
	else:
		sys.exit()

thread_5.join()
thread_4.join()
thread_1.join()