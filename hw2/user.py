#!/usr/bin/env python
import socket
import time
import struct
from ast import literal_eval as make_tuple
import threading
from threading import Thread
from threading import Lock
import sys

import pprint

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
groups_lock = Lock()

available_sock_id = 0
gm_tcp_port = -1
tcp_ip = -1

def print_dict(dct):
    print("{")
    for item, amount in dct.items():
        print("{} ({})".format(item, amount))
    print("}")
#################################################

class pollingThreadClass(Thread):
    def run(self):
        while 1:
            if gm_tcp_port == -1:
                time.sleep(0.01)
                continue

            polling_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            while 1:
                try:
                    polling_socket.connect((tcp_ip, gm_tcp_port))
                    print(YELLOW, "Successfully connected to TCP GM", ENDC)
                    break
                except :
                    continue

            print(YELLOW, "\n\n\nReceive TCP message", ENDC)
            try:
                data = polling_socket.recv(REQUEST_MES_SIZE)
            except ConnectionResetError:
                print(YELLOW, "GM closed connection while I was waiting for a command!", ENDC)
                polling_socket.close()
                continue

            if not data:
                continue
            print(YELLOW, "\tReceived ", data.decode(), ENDC)

            # Deal with the new information
            command, grp, u_id, I_am_new_sequencer = make_tuple(data.decode())
            if command == "JOINED":
                print(YELLOW, "New member in ", grp, ": ", u_id, ENDC)
                groups_lock.acquire()
                for sockid in groups:
                    (gname, users_no, mult_addr, my_id, isSequencer) = groups[sockid]
                    if gname == grp:
                        groups[sockid] = (gname, users_no+1, mult_addr, my_id, isSequencer)
                        print(RED, "JOINED: groups dict:")
                        print_dict(groups)
                        print(ENDC)
                        break
                groups_lock.release()
            elif command == "LEFT":
                print(YELLOW, u_id, " left ", grp, ENDC)
                if I_am_new_sequencer:
                    print(YELLOW, "and I am the new Sequencer!", ENDC)
                else:
                    print(YELLOW, "I still am not the Sequencer", ENDC)
                groups_lock.acquire()
                for sockid in groups:
                    (gname, users_no, mult_addr, my_id, _) = groups[sockid]
                    if gname == grp:
                        groups[sockid] = (gname, users_no-1, mult_addr, my_id, I_am_new_sequencer)
                        print(RED, "LEFT: groups dict:")
                        print_dict(groups)
                        print(ENDC)
                        break
                groups_lock.release()
            else:
                print(YELLOW, "received unknown message", ENDC)

            polling_socket.send(("ACK" + command).encode())

            polling_socket.close()

def establish_tcp_conn():
    global tcp_ip
    # Handshake to establish TCP connection (via Multicast)
    udp_s.sendto("TCP".encode(), (GM_MCAST_ADDR, GM_MCAST_PORT))
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
            time.sleep(1) # isws na vgei meta
            print("Going to try again")
    return s

#################################################
def join(gname, my_id):
    global available_sock_id
    global groups
    global gm_tcp_port
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
        users_no, multicast_addr, gm_tcp_port_local = ack_info
        print("gm_tcp_port_local = ", gm_tcp_port_local)
        if gm_tcp_port == -1:
            gm_tcp_port = gm_tcp_port_local
        if users_no == 1:
            isSequencer = True
        else:
            isSequencer = False
        groups_lock.acquire()
        groups[available_sock_id] = (gname, users_no, multicast_addr, my_id, isSequencer)
        groups_lock.release()
        available_sock_id += 1
        return available_sock_id - 1
    else:
        return -1

def leave(gsock_id):
    global groups
    global gm_tcp_port

    tcp_socket = establish_tcp_conn()

    # ready to send leave request to group manager
    (gname, _, _, user_id, _) = groups[gsock_id]
    args_to_send = (gname, user_id)
    tcp_socket.send(str(("LEAVE", args_to_send)).encode())
    print("Wait for GM to receive leave request")
    data = tcp_socket.recv(REQUEST_MES_SIZE)
    print("Received data: ", data.decode())
    tcp_socket.close()

    #check if it was successful or not
    ack_code, ack_info = make_tuple(data.decode())
    if ack_code == "L-ACK":
        groups_lock.acquire()
        del groups[gsock_id]
        if len(groups) == 0:
            gm_tcp_port = -1
        groups_lock.release()
        return 1
    elif ack_code == "L-N-ACK":
        return 0
    else:
        return -1

def grp_send(gsock_id, msg):
    pass

# return tuple of (msg_type, msg)
def grp_recv(gsock_id):
    pass
#################################################
# User code starts here

udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

# init polling thread
pollingThread = pollingThreadClass()
pollingThread.daemon = True
pollingThread.start()

user_id = input("Enter user name to put it in 'g1' and 'g2': ")
gsock_id_1 = join("g1", sys.argv[1])
gsock_id_2 = join("g2", sys.argv[1])
if gsock_id_1 == -1:# or gsock_id_2 == -1:
    exit()

time.sleep(5)

leave_res_1 = leave(gsock_id_1)
leave_res_2 = leave(gsock_id_2)

time.sleep(1)

# leave
udp_s.close()
