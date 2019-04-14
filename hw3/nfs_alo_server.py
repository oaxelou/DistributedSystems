import socket
import time
import struct
from ast import literal_eval as make_tuple
import threading
from threading import Thread
from threading import Lock
import sys
import random

RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
ENDC   = '\033[0m'

UDP_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_buf = {}
recv_buf_lock = Lock()
send_buf = {}
send_buf_lock = Lock()

################################# NFS STUFF ####################################
import os

############################################
O_CREAT = os.O_CREAT
O_EXCL = os.O_EXCL
O_TRUNC = os.O_TRUNC
O_RDWR = os.O_RDWR
O_RDONLY = os.O_RDONLY
O_WRONLY = os.O_WRONLY

SEEK_SET = os.SEEK_SET
SEEK_CUR = os.SEEK_CUR
SEEK_END = os.SEEK_END

FileExistsErrorCode = -1
FileNotFoundErrorCode = -2
BadFileDescriptorCode = -2

fid_dictionary = {}
next_fid = 0
############################################
def my_open(fname, mode):
    try:
        fid = os.open(fname, mode)
    except FileExistsError:
        print("File already exists. Going to return FileExistsErrorCode")
        return FileExistsErrorCode
    except FileNotFoundError:
        print("File does not exist. Going to return FileNotFoundErrorCode")
        return FileNotFoundErrorCode
    print("--------------------")
    print("File " + str(fid) + " has been created")
    print("--------------------")
    return fid
############################### END OF NFS STUFF ###############################

###########################    RECEIVER THREAD   ###############################

class Receiver(Thread):
    def run(self):
        global recv_buf
        global sock

        # always try to receive stuff
        while 1:
            d = sock.recvfrom(UDP_SIZE)
            data = d[0]
            addr = d[1]

            (RPC, reqID) = make_tuple(data.decode())
            req = (RPC, reqID, addr)

            recv_buf_lock.acquire()
            recv_buf[reqID] = req
            print("received:", recv_buf[reqID])
            recv_buf_lock.release()

############################    SENDER THREAD   ################################

class Sender(Thread):
    def run(self):
        global send_buf
        global sock

        while 1:
            if send_buf:
                send_buf_lock.acquire()

                # take reply with the min reqID
                min_reqID = min(send_buf, key=send_buf.get)
                reply2send = send_buf[min_reqID]

                print(GREEN, "going to send reply: ", reply2send, ENDC)

                addr = reply2send[2]
                sock.sendto(str(reply2send).encode(), (addr))

                del send_buf[min_reqID]
                send_buf_lock.release()

#######################    SERVER ADDRESS FUNCTIONS   ##########################
def get_IP():
    find_ip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        find_ip_sock.connect(('10.255.255.255', 1))
        IP = find_ip_sock.getsockname()[0]
    except:
        IP = '127.0.0.1'
    return IP

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

############################## MAIN THREAD #####################################

MY_IP = get_IP()
#  socket binding happens in here
MY_PORT = find_avl_port(sock, MY_IP)

print(MY_IP)
print(MY_PORT)

# init sender and receiver thread
senderthread = Sender()
receiverthread = Receiver()
senderthread.daemon = True
receiverthread.daemon = True
senderthread.start()
receiverthread.start()

while 1:
    if recv_buf:
        #  take a request from recv_buf (the one with the smaller reqID),
        #  process it and delete it from buffer
        recv_buf_lock.acquire()
        min_reqID = min(recv_buf, key=recv_buf.get)
        msg2proccess = recv_buf[min_reqID]
        print("going for req:", min_reqID)
        print("main thread: going to process:", min_reqID,":", msg2proccess)

        RPC = msg2proccess[0]
        reqID = msg2proccess[1]
        addr = msg2proccess[2]

        # compute
        if RPC[0] == "open":
            fname = RPC[1]
            flags = RPC[2]
            f = my_open(fname, O_CREAT | O_RDWR) # call my_open
            if f == FileExistsErrorCode:
                print("File already exists...")
                exit()
            elif f == FileNotFoundErrorCode:
                print("File does not exist...")
                exit()

            fid_dictionary[next_fid] = f
            next_fid += 1
            print(RED, fid_dictionary, ENDC)


        elif RPC[1] == "read":
            pass
        elif RPC[2] == "write":
            pass

        del recv_buf[min_reqID]

        # construct reply tuple/msg and add to send_buf
        reply_data = next_fid-1
        reply = (reply_data, reqID, addr)
        recv_buf_lock.release()

        # sender thread will take care of it
        send_buf_lock.acquire()
        send_buf[min_reqID] = reply
        send_buf_lock.release()
