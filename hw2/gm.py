#!/usr/bin/env python
import socket
import struct
import time
import random
from ast import literal_eval as make_tuple
from random import randint

RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
ENDC   = '\033[0m'

NON_PRIVILEGED_TCP_PORTS_START = 1024 #non-privileged ports: > 1023
TCP_PORT = 5016 #non-privileged ports: > 1023   ΑΥΤΟ ΔΕΝ ΧΡΕΙΑΖΕΤΑΙ
tcp_ports_being_used = []

GM_MCAST_ADDR = '224.0.0.1'
GM_MCAST_PORT = 10000

REQUEST_MES_SIZE = 1000  # Normally 1024, but we want fast response


GRPS_MCAST_ADDR = '224.0.0.2'
GRPS_MCAST_PORT = 1024
grp_ports_being_used = []
# initialization of groups dictionary
groups = {}

# UDP socket initialization
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
mreq = struct.pack("4sl", socket.inet_aton(GM_MCAST_ADDR), socket.INADDR_ANY)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
udp_s.bind((GM_MCAST_ADDR, GM_MCAST_PORT))
################################################################################

def find_first_available_tcp_port():
    print("\nSearch for the first available tcp port:")
    tcp_port = NON_PRIVILEGED_TCP_PORTS_START
    while tcp_port in tcp_ports_being_used:
        tcp_port += 1
    print("First available tcp_port: ", tcp_port)
    tcp_ports_being_used.append(tcp_port)
    return tcp_port
########################################################
def remove_tcp_port(tcp_port):
    if tcp_port in tcp_ports_being_used:
        tcp_ports_being_used.remove(tcp_port)
        print(tcp_port, " Successfully removed from list")
    else:
        print(tcp_port, " not in list")

def find_first_available_grp_port():
    print("\nSearch for the first available tcp port:")
    grp_port = NON_PRIVILEGED_TCP_PORTS_START
    while grp_port in grp_ports_being_used:
        grp_port += 1
    print("First available grp_port: ", grp_port)
    grp_ports_being_used.append(grp_port)
    return grp_port
########################################################
def remove_grp_port(grp_port):
    if grp_port in grp_ports_being_used:
        grp_ports_being_used.remove(grp_port)
        print(grp_port, " Successfully removed from grp list")
    else:
        print(grp_port, " not in grp list")
################################################################################

def establish_tcp_conn():
    while 1:
        print("\n\n\nGoing to wait for a udp message")
        d = udp_s.recvfrom(10)
        # print("Received message from ", d[1])
        if d[0].decode() == "TCP":
            tcp_port = find_first_available_tcp_port()
            udp_s.sendto(str(tcp_port).encode(), d[1])
            tcp_user_ip_addr, _ = d[1]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((tcp_user_ip_addr, tcp_port))
            s.listen(1)
            (conn, addr) = s.accept()
            return (s, conn, tcp_user_ip_addr, tcp_port)
        else:
            print("Received unknown message. Waiting for another one")
########################################################
def close_tcp_connection(conn, s, tcp_port, release_port_number):
    conn.close()
    s.close()
    if release_port_number == True:
        # Sto join den apodesmeuei to port epeidh ekei tha ginetai to polling!
        remove_tcp_port(tcp_port)
################################################################################

def join(conn, args, user_ip, user_gm_tcp_port):
    global groups
    g_name, user_id = args
    print(BLUE, '"', user_id, '" @', user_ip, ' wants to enter group "', g_name, '"', ENDC)
    # random_answer_generator = randint(0,1)
    # print("JOIN: going to return ", ("J-ACK" if (random_answer_generator == 1) else "J-N-ACK"))
    # if random_answer_generator:
    #     conn.send("J-ACK".encode())
    # else:
    #     conn.send("J-N-ACK".encode())

    if g_name in groups:
        # pass # NOT READY YET
        users_no, grp_addr, users_dict = groups[g_name]
        if user_id in users_dict:
            print(RED, user_id, " already in ", g_name, ENDC)
            conn.send(str(("J-N-ACK", 0)).encode())
        else:
            users_no += 1
            users_dict[user_id] = (user_ip , user_gm_tcp_port, False)
            groups[g_name] = (users_no, grp_addr, users_dict)
            # inform everyone that a new user joined the group
            print(GREEN, user_id, " added in ", g_name)
            print(groups, ENDC)
            conn.send(str(("J-ACK",(users_no , grp_addr))).encode())
    else:
        # add group in groups
        grp_addr = (GRPS_MCAST_ADDR, find_first_available_grp_port())
        users_dict = {user_id: (user_ip , user_gm_tcp_port, True)}
        # init Multicast socket for this group? here?
        groups[g_name] = (1, grp_addr, users_dict)
        print(GREEN, user_id, " added in ", g_name)
        print(groups, ENDC)
        conn.send(str(("J-ACK",(1 , grp_addr))).encode())


def leave(conn, args, user_ip, user_gm_tcp_port):
    global groups
    g_name, user_id = args
    print(BLUE, args, ENDC)
    users_no, grp_addr, users_dict = groups[g_name]

    if g_name not in groups or user_id not in users_dict:
        print(RED, user_id, " cannot be deleted from group ", g_name, ENDC)
        conn.send(str(("L-N-ACK", 0)).encode())
    else:
        (_, user_gm_tcp_port, isSequencer) = users_dict[user_id]
        print(grp_ports_being_used)
        print(tcp_ports_being_used)
        remove_tcp_port(user_gm_tcp_port)
        print(grp_ports_being_used)
        print(tcp_ports_being_used)
        if users_no > 1:
            users_no -= 1
            newSequencer = -1
            del users_dict[user_id]
            if isSequencer:
                print("Going to choose new Sequencer")
                newSequencer = random.choice(list(users_dict))
                (newSeq_ip , newSeq_gm_tcp_port, _) = users_dict[newSequencer]
                users_dict[newSequencer] = (newSeq_ip , newSeq_gm_tcp_port, True)

            # refresh group info
            groups[g_name] = (users_no, grp_addr, users_dict)

            # # wait for ack from users
        else:
            print("Empty group!")
            del groups[g_name]
            # release this port for other groups
            _, grp_port = grp_addr
            remove_grp_port(grp_port)

            # close udp Multicast socket of group
        print(GREEN,groups, ENDC)
        conn.send(str(("L-ACK",(1 , grp_addr))).encode())

########################################################
# GM code

while 1:
    (s, conn, user_ip, tcp_port) = establish_tcp_conn()
    print("\n\nTCP connection established!!")

    data = conn.recvfrom(REQUEST_MES_SIZE)
    print ("received data:", data)
    print("From ", data[1])
    # args: gname and user_id
    command, args = make_tuple(data[0].decode())
    if command == "JOIN":
        join(conn, args, user_ip, tcp_port)
        close_tcp_connection(conn, s, tcp_port, False)
    elif command == "LEAVE":
        leave(conn, args, user_ip, tcp_port)
        close_tcp_connection(conn, s, tcp_port, True)
    else:
        conn.send("WHAT?".encode())  # default answer when it doesn't know what to do
        close_tcp_connection(conn, s, tcp_port, True)

    print ("sent data:", data)


##################################
# Never reaches here
udp_s.close()
