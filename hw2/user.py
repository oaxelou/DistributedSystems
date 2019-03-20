#!/usr/bin/env python
import socket
import time
import struct
from ast import literal_eval as make_tuple

RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
ENDC   = '\033[0m'

GM_MCAST_ADDR = '224.0.0.1'
GM_MCAST_PORT = 10000

UDP_MES_SIZE = 100
REQUEST_MES_SIZE = 1000
MESSAGE = "Hello World"

SUCCESS = True
FAILURE = False

# initialization of the groups I'm in
groups = {}
available_sock_id = 0
gm_tcp_port = -1

def establish_tcp_conn():
    global gm_tcp_port
    # Handshake to establish TCP connection (via Multicast)
    udp_s.sendto("TCP".encode(), (GM_MCAST_ADDR, GM_MCAST_PORT))
    udp_address = udp_s.recvfrom(UDP_MES_SIZE)
    tcp_ip, _ = udp_address[1]
    gm_tcp_port = int(udp_address[0].decode())
    # Going to init TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while 1:
        print("Going to try to connect to TCP server")
        try:
            s.connect((tcp_ip, gm_tcp_port))
            print("Successfully connected to TCP")
            break
        except ConnectionRefusedError as notConnectedError:
            time.sleep(1) # isws na vgei meta
            print("Going to try again")
    return s

def join(gname, my_id):
    global available_sock_id
    global groups
    tcp_socket = establish_tcp_conn()
    # Ready to send request to GM!
    args_to_send = (gname, my_id)
    tcp_socket.send(str(("JOIN", args_to_send)).encode())
    print("Wait for GM to receive join request")
    data = tcp_socket.recv(REQUEST_MES_SIZE)
    print("Received data: ", data.decode())
    tcp_socket.close()
    # Check here if it's a success or a failure
    ack_code, ack_info = make_tuple(data.decode())
    if ack_code == "J-ACK":
        print("ack_info: ", ack_info)
        users_no, multicast_addr = ack_info
        if users_no == 1:
            isSequencer = True
        else:
            isSequencer = False
        groups[available_sock_id] = (gname, users_no, multicast_addr, isSequencer)
        available_sock_id += 1
        return available_sock_id - 1
    else:
        return -1
#################################################

# User code starts here

udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

grp_id = input("Enter grp_id: ")
user_id = input("Enter user_id: ")
gsock_id = join(grp_id, user_id)
if gsock_id >= 0:
    print("Successfully joined group stored in sockid: ", gsock_id)
    print(BLUE, "I can connect with GM through port ", gm_tcp_port, ENDC)
    print("Groups I belong in:")
    print(GREEN, groups, ENDC)
else:
    print("Failed at joining group")

# do stuff
# Check polling:
# Open thread that polls on the tcp connection

# leave

udp_s.close()
