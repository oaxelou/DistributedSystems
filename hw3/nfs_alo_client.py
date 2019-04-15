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
RESEND_TIMEOUT = 0.01

send_buf = {}
send_buf_lock = Lock()

recv_buf = {}
recv_buf_lock = Lock()

################################# NFS STUFF ####################################

import os

fid_local_dictionary = {}  # virtual_fid: (fid, pos)
next_local_fid = 0
# INIT_POS = 0
reqID = -1

# na kaneis sunarthsh na dilegei to prwto diathesimo virtual_fid
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
WrongWhenceCode = -3

def print_menu():
    menu_str  = "-----------------------\n" + "| Options:\n"
    menu_str += "| -> Open      a file (o)\n" + "| -> Read from a file (r)\n"
    menu_str += "| -> Write  on a file (w)\n"
    menu_str += "| -> Lseek  on a file (s)\n"
    menu_str += "| -> Close     a file (c)\n"
    menu_str += "| -> Print local dict (p)\n"
    menu_str += "| -> Exit (exit)\n"
    menu_str += "-----------------------\n" + "Enter answer: "
    return menu_str

def mynfs_open(fname, mode):
    global fid_local_dictionary
    # global INIT_POS
    global next_local_fid
    global reqID

    # instead of opening that locally, send RPC to server
    # fid = my_open(fname, mode)  # ONLY LOCALLY
    reqID += 1
    request = ("open", (fname, mode), reqID)
    send_buf_lock.acquire()
    send_buf[reqID] = request
    send_buf_lock.release()

    # print(fid_local_dictionary)
    # print(fid_local_dictionary)

    recv_buf_lock.acquire()
    while reqID not in recv_buf:
        recv_buf_lock.release()
        time.sleep(0.01)
        recv_buf_lock.acquire()

    print("Received answer for request: ", reqID)  # den to vgazei apo to recv_buf gia na anagnwrizei ta diplotupa!!!!
    print(BLUE, "And the reply is: ", recv_buf[reqID], ENDC)

    fid_local_dictionary[next_local_fid] = (recv_buf[reqID][0], 0, recv_buf[reqID][1])         #  apothikeuese kai to onoma tou arxeiou kai na to ektupwnei sto read
    recv_buf_lock.release()
    print("--------------------")
    print("OK: File " + str(next_local_fid) + " has been created")
    print("--------------------")

    next_local_fid += 1
    return next_local_fid-1

def mynfs_read(virtual_fid, nofBytes):
    global fid_local_dictionary
    global reqID

    if virtual_fid not in fid_local_dictionary:
        return (FileNotFoundErrorCode, 0)
    (fid, pos, _) = fid_local_dictionary[virtual_fid]

    reqID += 1
    request = ("read", (fid, pos, nofBytes), reqID)
    send_buf_lock.acquire()
    send_buf[reqID] = request
    send_buf_lock.release()

    # print(fid_local_dictionary)
    # fid_local_dictionary[next_local_fid] = (fid, INIT_POS)
    # print(fid_local_dictionary)

    recv_buf_lock.acquire()
    while reqID not in recv_buf:
        recv_buf_lock.release()
        time.sleep(0.01)
        recv_buf_lock.acquire()

    print("Received answer for request: ", reqID)  # den to vgazei apo to recv_buf gia na anagnwrizei ta diplotupa!!!!
    print(BLUE, "And the reply is: ", recv_buf[reqID], ENDC)
    (nofBytes, bytes_read, new_pos, new_size) = recv_buf[reqID]
    recv_buf_lock.release()

    fid_local_dictionary[virtual_fid] = (virtual_fid, new_pos, new_size)
    return (nofBytes, bytes_read.decode())

def mynfs_write(virtual_fid, buf):
    global fid_local_dictionary
    global reqID

    if virtual_fid not in fid_local_dictionary:
        return FileNotFoundErrorCode
    (fid, pos, _) = fid_local_dictionary[virtual_fid]

    reqID += 1
    request = ("write", (fid, pos, buf), reqID)
    send_buf_lock.acquire()
    send_buf[reqID] = request
    send_buf_lock.release()

    recv_buf_lock.acquire()
    while reqID not in recv_buf:
        recv_buf_lock.release()
        time.sleep(0.01)
        recv_buf_lock.acquire()

    print("Received answer for request: ", reqID)  # den to vgazei apo to recv_buf gia na anagnwrizei ta diplotupa!!!!
    print(BLUE, "And the reply is: ", recv_buf[reqID], ENDC)
    (bytes_written, new_pos, new_size) = recv_buf[reqID]
    recv_buf_lock.release()

    fid_local_dictionary[virtual_fid] = (virtual_fid, new_pos, new_size)
    return bytes_written

def mynfs_seek(virtual_fid, pos, whence):
    global fid_local_dictionary

    if virtual_fid not in fid_local_dictionary:
        return FileNotFoundErrorCode
    (fid, old_pos, size) = fid_local_dictionary[virtual_fid]
    # to set it to the position that the app sees (in case SEEK_CUR is set)
    if whence == SEEK_SET:
        start_pos = 0
    elif whence == SEEK_END:
        start_pos = size
    elif whence == SEEK_CUR:
        start_pos = old_pos
    else:
        return WrongWhenceCode

    fid_local_dictionary[virtual_fid] = (fid, start_pos + pos, size)
    return start_pos + pos

def mynfs_close(virtual_fid):
    global fid_local_dictionary
    if virtual_fid not in fid_local_dictionary:
        return FileNotFoundErrorCode
    (fid, _) = fid_local_dictionary[virtual_fid]
    del fid_local_dictionary[virtual_fid]
    # os.close(fid)                                                 # ONLY LOCALLY
    print("--------------------")
    print("File " + str(virtual_fid) + " removed")
    print("--------------------")

############################### END OF NFS STUFF ###############################

class Sender(Thread):
    def run(self):
        global send_buf
        global SERVER_IP, SERVER_PORT

        while 1:
            send_buf_lock.acquire()
            if send_buf:

                for req in send_buf:
                    message = send_buf[req]
                    sock.sendto(str(message).encode(), (SERVER_IP, SERVER_PORT))
                    print("sent request: ", message)

                # request will not be removed from send_buf
                # until receiver thread receives the corresponding reply
                # SOOOO Receiver thread has access to send_buf
                send_buf_lock.release()
                time.sleep(RESEND_TIMEOUT)
            else:
                send_buf_lock.release()

class Receiver(Thread):
    def run(self):
        global recv_buf

        while 1:
            d = sock.recvfrom(UDP_SIZE)
            data = d[0]
            # address is not needed: always expecting things from server
            # maybe check it is actually the server who sent sth

            recv_buf_lock.acquire()

            (reply, reqID) = make_tuple(data.decode())
            if reqID not in recv_buf.keys():
                recv_buf[reqID] = reply
                print("received reply: ", reply)
            else:
                print(RED, "DIPLOTYPO", ENDC)

            recv_buf_lock.release()
            send_buf_lock.acquire()
            if reqID in send_buf.keys():
                del send_buf[reqID]
            send_buf_lock.release()


################################### MAIN #######################################

# print("Enter server address and port:")
# SERVER_IP = input("address: ")
# SERVER_PORT = int(input("port: "))

if (len(sys.argv) != 3):
    print("args: server IP, server port")
    sys.exit()
SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
# print(SERVER_PORT, SERVER_IP)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

##########################
# This is going to be executed by mynfs_open/read/etc functions

# reqID = -1
#
# # put messages in send_buffer
# for i in range (10):
#     if i % 2 == 0:
#         text = "hello i am " + str(i)
#     else:
#         text = "my name is " + str(i)
#     reqID += 1
#
#     # i'm gonna leave that here as is, in case we need the message
#     # to be a tuple
#     message = (text, reqID)
#     send_buf_lock.acquire()
#     send_buf[reqID] = message
#     send_buf_lock.release()

# init sender and receiver thread
senderthread = Sender()
receiverthread = Receiver()
senderthread.daemon = True
receiverthread.daemon = True
senderthread.start()
receiverthread.start()

while True:
    option = input(print_menu())
    if option == 'o':
        fname = input("Enter file name to open: ") # Get name of file
        f = mynfs_open(fname, O_CREAT | O_RDWR) # call my_open
        if f == FileExistsErrorCode:
            print("File already exists...")
            exit()
        elif f == FileNotFoundErrorCode:
            print("File does not exist...")
            exit()


    elif option == 'r':
        fid = int(input("Enter fid: "))
        nofBytes = int(input("Enter nofBytes: "))
        bytes_read, bytes_buf = mynfs_read(fid, nofBytes)
        if bytes_read == BadFileDescriptorCode:
            print("Bad File Descriptor")
        else:
            print("I read ", bytes_read)
            print("And the value is: ", bytes_buf)


    elif option == 'w':
        fid = int(input("Enter fid: "))
        bytes_buf = input("Enter bytes to write: ")
        bytes_written = mynfs_write(fid, bytes_buf)
        if bytes_written == BadFileDescriptorCode:
            print("Bad File Descriptor")
        else:
            print("I wrote", bytes_written, "bytes")


    elif option == 's':
        fid = int(input("Enter fid: "))
        pos = int(input("Enter pos: "))
        whence = int(input("Enter whence([0 set] / [1 cur] / [2 end]) :"))
        current_pos = mynfs_seek(fid, pos, whence)
        if current_pos == WrongWhenceCode:
            print("Error in setting whence")
        else:
            print("Current pos: ", current_pos)

    elif option == 'p':
        print(GREEN, fid_local_dictionary, ENDC)


    elif option == 'exit':
        print("Byeeeeee")
        exit()


    elif option == 'bullshit':
        reqID += 1
        request = ("bullshit", 0, reqID)
        send_buf_lock.acquire()
        send_buf[reqID] = request
        send_buf_lock.release()

        recv_buf_lock.acquire()
        while reqID not in recv_buf:
            recv_buf_lock.release()
            time.sleep(0.01)
            recv_buf_lock.acquire()

        print("Received answer for request: ", reqID)  # den to vgazei apo to recv_buf gia na anagnwrizei ta diplotupa!!!!
        print(BLUE, "And the reply is: ", recv_buf[reqID][0], ENDC)
        recv_buf_lock.release()


    else:
        print("ignore")
