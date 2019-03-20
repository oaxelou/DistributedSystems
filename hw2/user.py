#!/usr/bin/env python
import socket
import time
import struct
from ast import literal_eval as make_tuple

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000

UDP_MES_SIZE = 100
REQUEST_MES_SIZE = 100
MESSAGE = "Hello World"

SUCCESS = True
FAILURE = False

def establish_tcp_conn():
    # Handshake to establish TCP connection (via Multicast)
    udp_s.sendto("TCP".encode(), (MCAST_GRP, MCAST_PORT))
    udp_address = udp_s.recvfrom(UDP_MES_SIZE)
    tcp_ip, _ = udp_address[1]
    tcp_port = int(udp_address[0].decode())
    # Going to init TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while 1:
        print("Going to try to connect to TCP server")
        try:
            s.connect((tcp_ip, tcp_port))
            print("Successfully connected to TCP")
            break
        except ConnectionRefusedError as notConnectedError:
            time.sleep(1)
            print("Going to try again")
    return s

def join():
    tcp_socket = establish_tcp_conn()
    # Ready to send request to GM!
    tcp_socket.send("JOIN".encode())
    print("Wait for GM to receive join request")
    data = tcp_socket.recv(REQUEST_MES_SIZE)
    print("Received data: ", data.decode())
    tcp_socket.close()
    # Check here if it's a success or a failure
    if data.decode() == "J-ACK":
        return SUCCESS
    else:
        return FAILURE
#################################################

# User code starts here

udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

joined_group_successfully = join()
if joined_group_successfully:
    print("Successfully joined group")
else:
    print("Failed at joining group")

# do stuff
# Check polling:
# Open thread that polls on the tcp connection

# leave

udp_s.close()
