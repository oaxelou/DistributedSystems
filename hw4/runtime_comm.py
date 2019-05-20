import socket
import sys
import time
import struct
import threading
from  threading import Lock
from threading import Thread
from ast import literal_eval as make_tuple
import struct

from parser import *  # temporary

FRAG_SIZE = 75
UDP_SIZE = FRAG_SIZE + 64

# The pinned Multicast address and port
MCAST_GRP  = '224.0.0.1'
MCAST_PORT = 10300

################################################################################
def find_avl_port(sock, MY_IP):
    UDP_PORT = 1
    while True:
        try:
            sock.bind((MY_IP, UDP_PORT))
        except PermissionError:
            # print("Another app is using this port. I am going to try try with: ", UDP_PORT)
            UDP_PORT += 1
            continue
        except OSError:
            # print("Another app is using this port. I am going to try try with: ", UDP_PORT)
            UDP_PORT += 1
            continue

            break

        print("I am listening on port: ", UDP_PORT)
        return UDP_PORT

def get_IP():
    find_ip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        find_ip_sock.connect(('10.255.255.255', 1))
        IP = find_ip_sock.getsockname()[0]
    except:
        IP = '127.0.0.1'
    return IP

def fragNsend(sock, prog_dict_entry, address):
    program_dictionary_string = str(prog_dict_entry)
    # print(program_dictionary_string)
    # print("#################################################")
    program_dictionary_serialized = program_dictionary_string.encode()
    # print(program_dictionary_serialized)

    sock.sendto(str(("migrate", 0)).encode(), address)

    iter = 0
    while True:
        # bytes2send = string2send[iter:(iter+25)].encode()
        bytes2send = program_dictionary_serialized[iter:(iter+FRAG_SIZE-1)]
        print("going to send ", bytes2send)
        sock.sendto(bytes2send, address)
        iter += FRAG_SIZE-1
        if iter >= len(program_dictionary_serialized.decode()):
            break
            # if iter >= len(string2send):
            #     break
        # time.sleep(2)
    # send exit
    message = "EndOfTransmission"
    sock.sendto(str(message).encode(), address)

def global_ids_update(sock, next_group_id, next_thread_id, my_load):
    message = ("inform", (next_group_id, next_thread_id, my_load))
    sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))

class MulticastListener(Thread):
    def run(self):
        while True:
            global next_group_id
            global next_thread_id
            # init - receive IP from the other runtime
            d = mult_sock.recvfrom(UDP_SIZE)
            print(MY_IP, MY_PORT)
            print(d[1])
            if d[1] == (MY_IP, MY_PORT):
                continue
            data = make_tuple(d[0].decode())
            if data[0] == "hello":
                print("New runtime @ ", d[1])
                ids_lock.acquire()
                other_runtimes_dict[d[1]] = 0
                # global_ids_update(sock, next_group_id, next_thread_id, my_load, d[1])
                message = ("inform", (next_group_id, next_thread_id, my_load))
                sock.sendto(str(message).encode(), d[1])
                print(other_runtimes_dict)
                ids_lock.release()
            elif data[0] == "exit":
                ids_lock.acquire()
                if d[1] in other_runtimes_dict:
                    del other_runtimes_dict[d[1]]
                    print(other_runtimes_dict)
                ids_lock.release()
            elif data[0] == "inform":
                ids_lock.acquire()
                next_group_id, next_thread_id, load = data[1]
                if d[1] not in other_runtimes_dict:
                    other_runtimes_dict[d[1]] = load
                    print(other_runtimes_dict)
                ids_lock.release()


class ReceiverThread(Thread):
    def run(self):
        while True:
            # init - receive IP from the other runtime
            d = sock.recvfrom(UDP_SIZE)
            data = make_tuple(d[0].decode())
            print("I got: ", data)
            if data[0] == "migrate":
                program_dictionary_serialized = ""
                while True:
                    d = sock.recvfrom(UDP_SIZE)
                    # print("I received from ", d[1])
                    data = d[0].decode()
                    # print("data: ", data)
                    if data == "EndOfTransmission":
                        break
                    program_dictionary_serialized += data
                program_dictionary_entry = make_tuple(program_dictionary_serialized)
                # print("#################################################")
                print(program_dictionary_entry)
                print("command 5: ", program_dictionary_entry[5][5])

                # ADD IN program_dictionary
                # 1) na pairnei to pedio tou threadID kai na to xrhsimopoiei ws key
                # 2) an uparxei sleep na prosarmozei ton xrono (h mhpws to runtime pou to stelnei?)
                # 3) na allaksoume tin IP (h mhpws to runtime pou to stelnei?)
            elif data[0] == "inform":
                ids_lock.acquire()
                next_group_id, next_thread_id, load = data[1]
                if d[1] not in other_runtimes_dict:
                    other_runtimes_dict[d[1]] = load
                    print(other_runtimes_dict)
                ids_lock.release()
################################################################################

# init private socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
MY_IP = get_IP()
MY_PORT = find_avl_port(sock, MY_IP)
print(MY_IP)
print(MY_PORT)

other_runtimes_dict = {}

# init program_dictionary
program_dictionary = {}
next_group_id = 0
next_thread_id = 0
my_load = 0

message = ("hello", 0)
sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))

# Multicast Socket creation
mult_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
mult_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
mult_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

mult_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
mult_sock.bind((MCAST_GRP, MCAST_PORT))

ids_lock = Lock()

# multicast thread
multicastthread = MulticastListener()
multicastthread.daemon = True
multicastthread.start()

receiverthread = ReceiverThread()
receiverthread.daemon = True
receiverthread.start()
#############################################################

def main():
    global next_group_id
    global next_thread_id
    # main part of the program
    input("Enter to start: ")

    ############################################
    # add program to program_dictionary
    program_name = "file2.txt"
    labels, instructions, error_code = parser(program_name)
    if error_code:
        print("Something wrong with parser")
        exit()
    program_dictionary[0] = (program_name, 0, 0, 0, 0, instructions, labels)

    ids_lock.acquire()
    next_group_id += 1
    next_thread_id += 1
    # inform for next_group_id & next_thread_id
    global_ids_update(sock, next_group_id, next_thread_id, my_load)
    ids_lock.release()

    ############################################
    # migration
    # if other_runtimes_dict:
    for i in range(2):
        for runtime in other_runtimes_dict:
            fragNsend(sock, program_dictionary[0], runtime)
            break
        time.sleep(2)
    print("Going to end now.")

main()
time.sleep(5)

message = ("exit", 0)
sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))
