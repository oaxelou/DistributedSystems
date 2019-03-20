#!/usr/bin/env python
import socket
import struct
import time
from ast import literal_eval as make_tuple
from random import randint

TCP_PORT = 5016 #non-privileged ports: > 1023

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000

BUFFER_SIZE = 20  # Normally 1024, but we want fast response

def establish_tcp_conn():
    while 1:
        print("\n\n\nGoing to wait for a udp message")
        d = udp_s.recvfrom(10)
        if d[0].decode() == "TCP":
            # print("Going to send TCP port: ", TCP_PORT)
            udp_s.sendto(str(TCP_PORT).encode(), d[1])
            tcp_user_ip_addr, _ = d[1]
            # print("Going to init TCP socket")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((tcp_user_ip_addr, TCP_PORT))
            # time.sleep(4)
            s.listen(1)
            # print("After listening to socket")
            # time.sleep(4)
            (conn, addr) = s.accept()
            # print ('Connection address:', addr)

            return (s, conn)
        else:
            print("Received unknown message. Waiting for another one")

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

udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
udp_s.bind((MCAST_GRP, MCAST_PORT))


while 1:
    (s, conn) = establish_tcp_conn()
    print("\n\nTCP connection established!!")

    data = conn.recv(BUFFER_SIZE)
    print ("received data:", data)
    if data.decode() == "JOIN":
        join(conn)
    else:
        conn.send("WHAT?".encode())  # default answer when it doesn't know what to do

    print ("sent data:", data)

    conn.close()
    s.close()
##################################
# Never reaches here
udp_s.close()
