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
udp_addr_to_tcp_port = {}  # dictionary that matches a certain user to the tcp port

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
        try:
            d = udp_s.recvfrom(10)
        except KeyboardInterrupt:
            print("GM going to exit...")
            exit()
        if d[0].decode() == "TCP":
            tcp_port = find_first_available_tcp_port()
            udp_s.sendto(str(tcp_port).encode(), d[1])
            print(RED, "TCP CONNECTION ON:", d[1], ENDC)
            tcp_user_ip_addr, _ = d[1]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((tcp_user_ip_addr, tcp_port))
            s.listen(1)
            (conn, addr) = s.accept()
            return (s, conn, d[1], tcp_port)
        else:
            print("Received unknown message. Waiting for another one")
########################################################
def close_tcp_connection(conn, s, tcp_port):
    conn.close()
    s.close()
    remove_tcp_port(tcp_port)
################################################################################

def inform_connection(tcp_ip, tcp_port, message):
    print(GREEN, "Going to init TCP socket", ENDC)
    print(GREEN, tcp_ip, " in port ", tcp_port, ENDC)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((tcp_ip, tcp_port))
    s.listen(1)
    print("After listening to socket")
    (conn, addr) = s.accept()

    conn.send(str(message).encode())
    print (GREEN, "sent data: ", str(message), ENDC)

    # Wait for ACK
    ack_rcv = conn.recv(REQUEST_MES_SIZE)
    if ack_rcv:
        command, _, _, _ = message
        if ack_rcv.decode() == ("ACK" + command):
            print (GREEN, "received ack:", ack_rcv.decode(), ENDC)
        else:
            print(GREEN, "I didn't receive the ack message I wanted. I received: ", ack_rcv.decode(), ENDC)
    conn.close()
    s.close()
################################################################################
def join(conn, args, user_udp_addr):
    global groups
    global udp_addr_to_tcp_port
    g_name, user_id = args
    print(BLUE, '"', user_id, '" @', user_udp_addr, ' wants to enter group "', g_name, '"', ENDC)

    if g_name in groups:
        # pass # NOT READY YET
        users_no, grp_addr, users_dict = groups[g_name]
        if user_id in users_dict:
            print(RED, user_id, " already in ", g_name, ENDC)
            conn.send(str(("J-N-ACK", 0)).encode())
        else:
            users_no += 1
            for user in users_dict:
                (user_ip, user_gm_tcp_port, _) = users_dict[user]
                inform_connection(user_ip, user_gm_tcp_port, ("JOINED", g_name, user_id, 0)) # not using the last parameter

            # Add new user to the group
            user_ip_addr, user_tcp_port = user_udp_addr
            if user_udp_addr in udp_addr_to_tcp_port:
                no_groups_member_in, user_gm_tcp_port = udp_addr_to_tcp_port[user_udp_addr]
                udp_addr_to_tcp_port[user_udp_addr] = (no_groups_member_in + 1, user_gm_tcp_port)
            else:
                user_gm_tcp_port = find_first_available_tcp_port()
                udp_addr_to_tcp_port[user_udp_addr] = (1, user_gm_tcp_port)
            users_dict[user_id] = (user_ip_addr , user_gm_tcp_port, False)
            groups[g_name] = (users_no, grp_addr, users_dict)

            print(GREEN, user_id, " added in ", g_name)
            print(groups, ENDC)
            conn.send(str(("J-ACK",(users_no , grp_addr, user_gm_tcp_port))).encode())
    else:
        # add group in groups
        grp_addr = (GRPS_MCAST_ADDR, find_first_available_grp_port())
        user_ip_addr, user_tcp_port = user_udp_addr
        if user_udp_addr in udp_addr_to_tcp_port:
            print(GREEN, "INFO: ", udp_addr_to_tcp_port[user_udp_addr])
            no_groups_member_in, user_gm_tcp_port = udp_addr_to_tcp_port[user_udp_addr]
            udp_addr_to_tcp_port[user_udp_addr] = (no_groups_member_in + 1, user_gm_tcp_port)
        else:
            user_gm_tcp_port = find_first_available_tcp_port()
            udp_addr_to_tcp_port[user_udp_addr] = (1, user_gm_tcp_port)
            print(GREEN, "xINFO: ", udp_addr_to_tcp_port[user_udp_addr])

        users_dict = {user_id: (user_ip_addr , user_gm_tcp_port, True)}
        # init Multicast socket for this group? here?
        groups[g_name] = (1, grp_addr, users_dict)
        print(GREEN, user_id, " added in ", g_name, " with gm_tcp_port: ", user_gm_tcp_port)
        print(groups, ENDC)
        conn.send(str(("J-ACK",(1 , grp_addr, user_gm_tcp_port))).encode())

def leave(conn, args, user_udp_addr):
    global groups
    global udp_addr_to_tcp_port
    g_name, user_id = args
    print(BLUE, args, ENDC)
    users_no, grp_addr, users_dict = groups[g_name]

    if g_name not in groups or user_id not in users_dict:
        print(RED, user_id, " cannot be deleted from group ", g_name, ENDC)
        conn.send(str(("L-N-ACK", 0)).encode())
    else:
        (_, user_gm_tcp_port, isSequencer) = users_dict[user_id]
        if user_udp_addr not in udp_addr_to_tcp_port:
            print(BLUE, udp_addr_to_tcp_port, ENDC)
            print(RED, "SOMETHING IS TERRIBLY WRONG!", ENDC)
        no_groups_member_in, user_gm_tcp_port = udp_addr_to_tcp_port[user_udp_addr]
        udp_addr_to_tcp_port[user_udp_addr] = (no_groups_member_in - 1, user_gm_tcp_port)
        print(BLUE, udp_addr_to_tcp_port, ENDC)
        print(BLUE, user_gm_tcp_port, ":", no_groups_member_in, ENDC)
        if no_groups_member_in - 1 == 0:
            print(RED, "Going to remove ", user_udp_addr, ENDC)
            remove_tcp_port(user_gm_tcp_port)
            del udp_addr_to_tcp_port[user_udp_addr]
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
            for user in users_dict:
                (user_ip, user_gm_tcp_port, isSequencer) = users_dict[user]
                inform_connection(user_ip, user_gm_tcp_port, ("LEFT", g_name, user_id, isSequencer)) # not using the last parameter

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
    (s, conn, user_udp_addr, tcp_port) = establish_tcp_conn()
    print("\n\nTCP connection established!!")

    data = conn.recvfrom(REQUEST_MES_SIZE)
    print ("received data:", data)
    print("From ", data[1])
    # args: gname and user_id
    command, args = make_tuple(data[0].decode())
    print(YELLOW, "groups: ", grp_ports_being_used, ENDC)
    print(YELLOW, "tcps  : ", tcp_ports_being_used, ENDC)
    if command == "JOIN":
        join(conn, args, user_udp_addr)
        close_tcp_connection(conn, s, tcp_port)
    elif command == "LEAVE":
        leave(conn, args, user_udp_addr)
        close_tcp_connection(conn, s, tcp_port)
    else:
        conn.send("WHAT?".encode())  # default answer when it doesn't know what to do
        close_tcp_connection(conn, s, tcp_port)

    print(YELLOW, "groups: ", grp_ports_being_used, ENDC)
    print(YELLOW, "tcps  : ", tcp_ports_being_used, ENDC)
    print ("sent data:", data)


##################################
# Never reaches here
udp_s.close()
