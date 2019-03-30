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
groups_lock = Lock()

receiveThreads = {}
sendThreads = {}
sockets = {}

available_sock_id = 0
gm_tcp_port = -1
tcp_ip = -1

msges_to_send = {}
msg_lock = Lock()

current_seqNO = {}
my_seqNO = {}
messageID = 0
BACK_OFF = 0.1

NO_MSG_CODE   = 0
GM_MSG_CODE   = 1
USER_MSG_CODE = 2

def init_socket(mult_addr):
    ip, port = mult_addr
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.bind(mult_addr)
    return sock
################################################################################
def print_dict(dct):
    print("{")
    for item, amount in dct.items():
        print("{} ({})".format(item, amount))
    print("}")
################################################################################
def RM_send(gsock_id, msg):
    # pass
    global groups
    global sockets

    groups_lock.acquire()
    (_, users_no, mult_addr, _, _, _, _, acks_dict) = groups[gsock_id]
    acks_no = 0
    (msgID, _, _, sender_name) = msg
    acks_dict[(msgID, sender_name)] = 0
    groups_lock.release()

    sockets[gsock_id].sendto(str(msg).encode(), mult_addr)
    # epanaleiptika n koitaei thn acks_dict mexri na tou exoun erthei ola
    # print(YELLOW, 'for acks: usersno: ', users_no, ENDC)
    while acks_no < users_no - 1:
        groups_lock.acquire()
        # print(YELLOW, "acks_dict: ", acks_dict[(msgID, sender_name)], ENDC)
        if acks_dict[(msgID, sender_name)] > 0: # not empty
            acks_no += 1
            # print(YELLOW, "acks got: ", acks_no, ENDC)
            if acks_no == users_no - 1:
                del acks_dict[(msgID, sender_name)]
        # if len(list(acks_dict)) > 0: # not empty
        #     acks_no += 1
        #     print(YELLOW,"acks got: ", acks_no, ENDC)
        #     acks_dict.pop()
        # else:
            # time.sleep(BACK_OFF)
            # sockets[gsock_id].sendto(str(msg).encode(), mult_addr)
        groups_lock.release()
        time.sleep(0.001)
    # print(GREEN,"Got all acks for: ", msg, ENDC)

def RM_rcv(gsock_id):
    # pass
    global sockets
    global groups
    groups_lock.acquire()
    (_, _, mult_addr, _, _, _, _, acks_dict) = groups[gsock_id]
    groups_lock.release()
    while 1:
        data = sockets[gsock_id].recvfrom(1024)
        (ID_to_check, msg, _, sender_name) = make_tuple(data[0].decode())
        # print(BLUE, msg, "from ", data[1], ENDC)
        if not(msg == "ACK"):
            msgID = ID_to_check
            # print(YELLOW,"Going to send ack",ENDC)
            sockets[gsock_id].sendto(str((msgID, "ACK", 0, sender_name)).encode(), mult_addr)
            break
        else:
            groups_lock.acquire()
            if (ID_to_check, sender_name) in acks_dict:
                acks_dict[(ID_to_check, sender_name)] += 1
                # print(GREEN,"Got ack",ENDC)
            # else:
                # print("ACK not for me")
            groups_lock.release()
        # print(BLUE, "show must go on", ENDC)
    # print(GREEN,"received: ", msg, ENDC)
    return data
################################################################################
class Sender(Thread):
    def __init__(self, socket, gsock_id):
        Thread.__init__(self)
        self.socket = socket
        self.gsock_id = gsock_id

    def run(self):
        global groups
        global messageID

        groups_lock.acquire()
        (grp_name, users_no, mult_addr, my_id, _, _, _, _) = groups[self.gsock_id]
        groups_lock.release()

        while 1:
            msg_lock.acquire()
            if msges_to_send[self.gsock_id]:
                msg = msges_to_send[self.gsock_id].pop()
                # print("Found a msg to send: ", msg)
            else:
                msg_lock.release()
                time.sleep(0.001)
                continue
            msg_lock.release()

            msg = (messageID, msg, -1, my_id)
            # RM_send
            # sockets[self.gsock_id].sendto(str(msg).encode(), mult_addr)
            RM_send(self.gsock_id, msg)
            print("The message has been sent")
            messageID += 1
################################################################################
class Receiver(Thread):
    def __init__(self, socket, gsock_id):
        Thread.__init__(self)
        self.socket = socket
        self.gsock_id = gsock_id

    def run(self):
        global groups
        global current_seqNO
        sock = sockets[self.gsock_id]
        msgdict = {}
        (_, _, grp_addr, _, isSequencer, _, _, _) = groups[self.gsock_id]
        while 1:
            try:
                # RM_rcv
                # data = sock.recvfrom(1024)
                data = RM_rcv(self.gsock_id)
            except OSError:
                print("Going to terminate the thread")
                break
            if not data:
                print("Going to terminate the thread")
                break

            # print(RED, "Received: ", data[0], ENDC)
            (msgID, msg, seqNO, sender_name) = make_tuple(data[0].decode())
            if seqNO == -1:  # Did not receive a seq_no_msg
                msgID = (data[1], msgID)
                if isSequencer:
                    seq_no_msg = (msgID, "-", current_seqNO[self.gsock_id], "-")
                    # RM_send
                    try:
                        # RM_send(self.gsock_id, seq_no_msg)
                        sock.sendto(str(seq_no_msg).encode(), grp_addr)
                    except OSError:
                        break
                    current_seqNO[self.gsock_id] += 1
            if msgID in msgdict:
                (old_msg, old_seqNO, old_sender_name) = msgdict[msgID]
                if old_seqNO != -1 and seqNO == -1:
                    msgdict[msgID] = (msg, old_seqNO, sender_name)
                    groups_lock.acquire()
                    (grp_name, users_no, mult_addr, my_id, isSequencer, msg_received, _, acks_dict) = groups[self.gsock_id]
                    # msg_received[msgID] = msgdict[msgID]
                    msg_received[old_seqNO] = msgdict[msgID]
                    # print(msgID, ":", msgdict[msgID] , "added to msg_received")
                    del msgdict[msgID]
                    groups_lock.release()
                elif old_seqNO == -1 and seqNO != -1:
                    msgdict[msgID] = (old_msg, seqNO, old_sender_name)
                    groups_lock.acquire()
                    (grp_name, users_no, mult_addr, my_id, isSequencer, msg_received, _, acks_dict) = groups[self.gsock_id]
                    # msg_received[msgID] = msgdict[msgID]
                    msg_received[seqNO] = msgdict[msgID]
                    # print(msgID, ":", msgdict[msgID] , "ADDED to msg_received")
                    del msgdict[msgID]
                    groups_lock.release()
            else:
                msgdict[msgID] = (msg, seqNO, sender_name)

            # print(RED, "msgdict: ", msgdict, ENDC)

        # Out of the while
        print(RED, "terminating receive thread", ENDC)
################################################################################
class pollingThreadClass(Thread):
    def run(self):
        while 1:
            if gm_tcp_port == -1:
                time.sleep(0.0001)
                continue

            polling_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            while 1:
                try:
                    polling_socket.connect((tcp_ip, gm_tcp_port))
                    # print(YELLOW, "Successfully connected to TCP GM", ENDC)
                    break
                except :
                    continue

            # print(YELLOW, "\n\n\nReceive TCP message", ENDC)
            try:
                data = polling_socket.recv(REQUEST_MES_SIZE)
            except ConnectionResetError:
                # print(YELLOW, "GM closed connection while I was waiting for a command!", ENDC)
                polling_socket.close()
                continue

            if not data:
                continue
            # print(YELLOW, "\tReceived ", data.decode(), ENDC)

            # Deal with the new information
            command, grp, u_id, I_am_new_sequencer = make_tuple(data.decode())
            if command == "JOINED":
                # print(YELLOW, "New member in ", grp, ": ", u_id, ENDC)
                groups_lock.acquire()
                for sockid in groups:
                    (gname, users_no, mult_addr, my_id, isSequencer, msg_received, gm_msges, acks_dict) = groups[sockid]
                    if gname == grp:
                        groups[sockid] = (gname, users_no+1, mult_addr, my_id, isSequencer, msg_received, gm_msges, acks_dict)
                        gm_msg = u_id + " joined " + grp
                        gm_msges.append(gm_msg)
                        break
                groups_lock.release()
            elif command == "LEFT":
                groups_lock.acquire()
                for sockid in groups:
                    (gname, users_no, mult_addr, my_id, _, msg_received, gm_msges, acks_dict) = groups[sockid]
                    if gname == grp:
                        groups[sockid] = (gname, users_no-1, mult_addr, my_id, I_am_new_sequencer, msg_received, gm_msges, acks_dict)
                        gm_msg = u_id + " left " + grp
                        gm_msges.append(gm_msg)
                        break
                groups_lock.release()
            # else:
                # print(YELLOW, "received unknown message", ENDC)

            polling_socket.send(("ACK" + command).encode())

            polling_socket.close()
################################################################################
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
        # print("Going to try to connect to TCP server")
        try:
            s.connect((tcp_ip, tcp_port))
            # print("Successfully connected to TCP")
            break
        except ConnectionRefusedError as notConnectedError:
            time.sleep(0.1) # isws na vgei meta
            # print("Going to try again")
    return s

#################################################
def join(gname, my_id):
    global available_sock_id
    global groups
    global gm_tcp_port
    global receiveThread
    tcp_socket = establish_tcp_conn()
    # Ready to send request to GM!
    args_to_send = (gname, my_id)
    tcp_socket.send(str(("JOIN", args_to_send)).encode())
    # print("Wait for GM to receive join request")
    data = tcp_socket.recv(REQUEST_MES_SIZE)
    # print("Received data: ", data.decode())
    tcp_socket.close()

    # Check here if it's a success or a failure
    ack_code, ack_info = make_tuple(data.decode())
    if ack_code == "J-ACK":
        # print("ack_info: ", ack_info)
        users_no, multicast_addr, gm_tcp_port_local = ack_info
        # print("gm_tcp_port_local = ", gm_tcp_port_local)
        if gm_tcp_port == -1:
            gm_tcp_port = gm_tcp_port_local
        if users_no == 1:
            isSequencer = True
        else:
            isSequencer = False
        groups_lock.acquire()
        groups[available_sock_id] = (gname, users_no, multicast_addr, my_id, isSequencer, {}, [], {})

        my_seqNO[available_sock_id] = 0
        current_seqNO[available_sock_id] = 0
        sockets[available_sock_id] = init_socket(multicast_addr)

        receiveThreads[available_sock_id] = Receiver(sockets[available_sock_id], available_sock_id)
        receiveThreads[available_sock_id].daemon = True
        receiveThreads[available_sock_id].start()

        sendThreads[available_sock_id] = Sender(sockets[available_sock_id], available_sock_id)
        sendThreads[available_sock_id].daemon = True
        sendThreads[available_sock_id].start()

        msges_to_send[available_sock_id] = []
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
    (gname, _, _, user_id, _, _, _, _) = groups[gsock_id]
    args_to_send = (gname, user_id)
    tcp_socket.send(str(("LEAVE", args_to_send)).encode())
    # print("Wait for GM to receive leave request")
    data = tcp_socket.recv(REQUEST_MES_SIZE)
    # print("Received data: ", data.decode())
    tcp_socket.close()

    #check if it was successful or not
    ack_code, ack_info = make_tuple(data.decode())
    if ack_code == "L-ACK":
        groups_lock.acquire()
        sockets[gsock_id].close()
        del current_seqNO[gsock_id]
        del my_seqNO[gsock_id]
        del sockets[gsock_id]
        del receiveThreads[gsock_id]
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
    msg_lock.acquire()
    msges_to_send[gsock_id].append(msg)
    msg_lock.release()

# return tuple of (msg_type, msg)
def grp_recv(gsock_id):
    global my_seqNO

    groups_lock.acquire()
    (grp_name, users_no, mult_addr, my_id, isSequencer, msg_received, gm_msges, acks_dict) = groups[gsock_id]
    if (not msg_received) and (not gm_msges):
        # print("No message available")
        groups_lock.release()
        return (NO_MSG_CODE, 0)

    if gm_msges:
        return_msg = (GM_MSG_CODE, gm_msges.pop())
        groups_lock.release()
        return return_msg

    # print(GREEN, "Messages received: ", msg_received, ENDC)
    # print(BLUE, "My seqNO: ", my_seqNO[gsock_id], ENDC)
    if my_seqNO[gsock_id] in msg_received:
        (msg, seqNO, sender_name) = msg_received[my_seqNO[gsock_id]]
        msg = sender_name + ": " + msg
        return_msg = (USER_MSG_CODE, msg)
        del msg_received[my_seqNO[gsock_id]]
        my_seqNO[gsock_id] += 1
        groups_lock.release()
        return return_msg

    groups_lock.release()
    return (NO_MSG_CODE, 0)
#################################################
# User code starts here

udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

# init polling thread
pollingThread = pollingThreadClass()
pollingThread.daemon = True
pollingThread.start()

# # time.sleep(3)
# gsock_id_1 = join("g1", sys.argv[1])
# gsock_id_2 = join("g2", sys.argv[1])
# if gsock_id_1 == -1:# or gsock_id_2 == -1:
#     exit()
#
# input("Press enter to start communication: ")
#
# try:
#     while 1:
#         print("Message buckets:")
#         while 1:
#             (msg_type, msg) = grp_recv(gsock_id_1)
#             if msg_type == GM_MSG_CODE:
#                 print("G1: ", YELLOW, msg, ENDC)
#             elif msg_type == USER_MSG_CODE:
#                 print("G1: ", BLUE, msg, ENDC)
#             else:
#                 break
#         while 1:
#             (msg_type, msg) = grp_recv(gsock_id_2)
#             if msg_type == GM_MSG_CODE:
#                 print("G2: ", YELLOW, msg, ENDC)
#             elif msg_type == USER_MSG_CODE:
#                 print("G2: ", BLUE, msg, ENDC)
#             else:
#                 break
#         time.sleep(4)
#         # if sys.argv[1] == "oly":
#         grp_send(gsock_id_1, input("Send message to grp1: "))
#         grp_send(gsock_id_2, input("Send message to grp2: "))
#         time.sleep(4)
# except KeyboardInterrupt:
#     print("Pressed ctrl+C to exit!")
#
# print("Going to leave")
# leave_res_1 = leave(gsock_id_1)
# leave_res_2 = leave(gsock_id_2)

# # leave
# udp_s.close()
