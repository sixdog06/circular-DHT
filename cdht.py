# written by python 3.7.1

import sys
import time
from socket import *

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
clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + first_successive_id))
time.sleep(0.5) # wait for 0.5 second
clientSocket.sendto(str(own_id).encode(), ('127.0.0.1', 50000 + second_successive_id))

# ping server
serverPort = 50000 + own_id
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('127.0.0.1', serverPort))

while True:
    data, addr = serverSocket.recvfrom(1024)
    #time.sleep(0.5)
    print(f'A ping request message was received from Peer {data.decode()}.')
    serverSocket.sendto(str(own_id).encode(), addr)


