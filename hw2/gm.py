#!/usr/bin/env python
import socket
import struct
import time
from ast import literal_eval as make_tuple
from random import randint

NON_PRIVILEGED_TCP_PORTS_START = 1024 #non-privileged ports: > 1023
TCP_PORT = 5016 #non-privileged ports: > 1023
tcp_ports_being_used = []

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000

REQUEST_MES_SIZE = 20  # Normally 1024, but we want fast response

# UDP socket initialization
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
udp_s.bind((MCAST_GRP, MCAST_PORT))

def find_first_available_tcp_port():
    print("\nSearch for the first available tcp port:")
    tcp_port = NON_PRIVILEGED_TCP_PORTS_START
    while tcp_port in tcp_ports_being_used:
        tcp_port += 1
    print("First available tcp_port: ", tcp_port)
    tcp_ports_being_used.append(tcp_port)
    return tcp_port

def remove_tcp_port(tcp_port):
    if tcp_port in tcp_ports_being_used:
        tcp_ports_being_used.remove(tcp_port)
        print(tcp_port, " Successfully removed from list")
    else:
        print(tcp_port, " not in list")
################################################################################
def establish_tcp_conn():
    while 1:
        print("\n\n\nGoing to wait for a udp message")
        d = udp_s.recvfrom(10)
        if d[0].decode() == "TCP":
            tcp_port = find_first_available_tcp_port()
            udp_s.sendto(str(tcp_port).encode(), d[1])
            tcp_user_ip_addr, _ = d[1]
            # print("Going to init TCP socket")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((tcp_user_ip_addr, tcp_port))
            # time.sleep(4)
            s.listen(1)
            # print("After listening to socket")
            # time.sleep(4)
            (conn, addr) = s.accept()
            # print ('Connection address:', addr)

            return (s, conn, tcp_port)
        else:
            print("Received unknown message. Waiting for another one")

def close_tcp_connection(conn, s, tcp_port):
    conn.close()
    s.close()
    remove_tcp_port(tcp_port)
########################################################
def join(conn):
    random_answer_generator = randint(0,1)
    print("JOIN: going to return ", ("J-ACK" if (random_answer_generator == 1) else "J-N-ACK"))
    if random_answer_generator:
        conn.send("J-ACK".encode())
    else:
        conn.send("J-N-ACK".encode())

########################################################
# GM code

while 1:
    (s, conn, tcp_port) = establish_tcp_conn()
    print("\n\nTCP connection established!!")

    data = conn.recv(REQUEST_MES_SIZE)
    print ("received data:", data)
    if data.decode() == "JOIN":
        join(conn)
    else:
        conn.send("WHAT?".encode())  # default answer when it doesn't know what to do

    print ("sent data:", data)

    close_tcp_connection(conn, s, tcp_port)

##################################
# Never reaches here
udp_s.close()
