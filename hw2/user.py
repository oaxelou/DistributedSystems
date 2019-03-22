#!/usr/bin/env python
import socket
import time
import struct
from ast import literal_eval as make_tuple
import threading
from threading import Thread
from threading import Lock
import sys

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
tcp_ip = -1

class pollingThreadClass(Thread):
    def run(self):
        while 1:
            if gm_tcp_port == -1:
                # print(YELLOW, "Not in any group...", ENDC)
                time.sleep(0.01)
                continue

            polling_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            while 1:
                # print(YELLOW, "Going to try to connect to TCP server", ENDC)
                try:
                    polling_socket.connect((tcp_ip, gm_tcp_port))
                    print(YELLOW, "Successfully connected to TCP GM", ENDC)
                    break
                except :
                    # time.sleep(2)
                    # print(YELLOW, "Going to try again", ENDC)
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

            # Originally, it would send back ACK message  HERE

            # Deal with the new information
            command, grp, u_id, I_am_new_sequencer = make_tuple(data.decode())
            if command == "JOINED":
                print(YELLOW, "New member in ", grp, ": ", u_id, ENDC)
            elif command == "LEFT":
                print(YELLOW, u_id, " left ", grp, ENDC)
                if I_am_new_sequencer:
                    print(YELLOW, "and I am the new Sequencer!", ENDC)
                else:
                    print(YELLOW, "I still am not the Sequencer", ENDC)
                # groups[available_sock_id] = (gname, users_no, multicast_addr, isSequencer)

            # print(YELLOW, "Connection closed?", ENDC)
            polling_socket.close()
            # print(YELLOW, "Connection closed", ENDC)

            # time.sleep(1)


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
        groups[available_sock_id] = (gname, users_no, multicast_addr, my_id, isSequencer)
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
    # user_id = "oly"
    args_to_send = (gname, user_id)
    tcp_socket.send(str(("LEAVE", args_to_send)).encode())
    print("Wait for GM to receive leave request")
    data = tcp_socket.recv(REQUEST_MES_SIZE)
    print("Received data: ", data.decode())
    tcp_socket.close()

    #check if it was successful or not
    ack_code, ack_info = make_tuple(data.decode())
    if ack_code == "L-ACK":
        del groups[gsock_id]
        if len(groups) == 0:
            gm_tcp_port = -1
        return 1
    elif ack_code == "L-N-ACK":
        return 0
    else:
        return -1

#################################################

# User code starts here

udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)


# init polling thread
pollingThread = pollingThreadClass()
pollingThread.daemon = True
pollingThread.start()

# grp_id = input("Enter grp_id: ")
# user_id = input("Enter user_id: ")
# gsock_id = join(grp_id, user_id)
# if gsock_id >= 0:
#     print("Successfully joined group stored in sockid: ", gsock_id)
#     print(BLUE, "I can connect with GM through port ", gm_tcp_port, ENDC)
#     print("Groups I belong in:")
#     print(GREEN, groups, ENDC)
# else:
#     print("Failed at joining group")
#     exit()

user_id = input("Enter user name to put it in 'g1' and 'g2': ")
gsock_id_1 = join("g1", sys.argv[1])
gsock_id_2 = join("g2", sys.argv[1])
if gsock_id_1 == -1:# or gsock_id_2 == -1:
    exit()

time.sleep(5)

leave_res_1 = leave(gsock_id_1)
leave_res_2 = leave(gsock_id_2)

# do stuff and then leave
# if len(sys.argv) == 2 and sys.argv[1].isdigit():
#     time.sleep(int(sys.argv[1]))
# else:
#     time.sleep(5)
# leave_res = leave(gsock_id)
# if leave_res == 1:
#     print("Successfully left group stored in sockid: ", gsock_id)
#     print("fuck these losers")
#     print("Groups I belong in:") #should be empty for now
#     print(GREEN, groups, ENDC)
# else:
#     print("Failed at leaving group")

time.sleep(1)
# do stuff
# Check polling:
# Open thread that polls on the tcp connection

# leave

udp_s.close()
