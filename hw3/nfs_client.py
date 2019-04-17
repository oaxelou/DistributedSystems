import socket
import time
import struct
from ast import literal_eval as make_tuple
import threading
from threading import Thread
from threading import Lock
import sys
import random
import os

################################# NFS STUFF ####################################
CACHE_TOTAL_SIZE = 32          # max megethos mnhmhs cache
CACHE_BLOCK_SIZE = 10          # kanonika einai 1024
CACHE_BLOCK_FRESHNESS = 20     # kanonika poso?
cache_size = 0

fid_local_dictionary = {}      # virtual_fid: (fid, pos)
reqID = -1

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
PermissionDeniedErrorCode = -4

############################# OTHER STUFF  ####################################
RESEND_TIMEOUT = 0.1
UDP_SIZE = 1024

send_buf = {}
send_buf_lock = Lock()

recv_buf = {}
recv_buf_lock = Lock()

RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
ENDC   = '\033[0m'

############################### RPC FUNCTIONS ###############################
def openRPC(fname, mode):
    global reqID
    reqID += 1
    request = ("open", (fname, mode), reqID)
    send_buf_lock.acquire()
    send_buf[reqID] = request
    send_buf_lock.release()

    recv_buf_lock.acquire()
    while reqID not in recv_buf:
        recv_buf_lock.release()
        time.sleep(0.001)
        recv_buf_lock.acquire()

    recv_buf_lock.release()
    return recv_buf[reqID]

def readRPC(fid, key):
    global reqID

    reqID += 1
    request = ("read", (fid, CACHE_BLOCK_SIZE * key, CACHE_BLOCK_SIZE), reqID)
    send_buf_lock.acquire()
    send_buf[reqID] = request
    send_buf_lock.release()

    recv_buf_lock.acquire()
    while reqID not in recv_buf:
        recv_buf_lock.release()
        time.sleep(0.001)
        recv_buf_lock.acquire()

    (nofBytes, bytes_read, new_pos, new_size) = recv_buf[reqID]
    recv_buf_lock.release()
    return (nofBytes, bytes_read, new_pos, new_size)

def writeRPC(fid, pos, buf):
    global reqID
    reqID += 1
    request = ("write", (fid, pos, buf), reqID)
    send_buf_lock.acquire()
    send_buf[reqID] = request
    send_buf_lock.release()

    recv_buf_lock.acquire()
    while reqID not in recv_buf:
        recv_buf_lock.release()
        time.sleep(0.001)
        recv_buf_lock.acquire()

    (bytes_written, new_pos, new_size) = recv_buf[reqID]
    recv_buf_lock.release()
    return (bytes_written, new_pos, new_size)

############################### NFS FUNCTIONS ###############################
def mynfs_open(fname, mode):
    global fid_local_dictionary

    (fid, new_size) = openRPC(fname, mode)
    if fid >= 0:
        next_local_fid = 0
        while next_local_fid in fid_local_dictionary.keys():
            next_local_fid += 1
        fid_local_dictionary[next_local_fid] = (fname, mode, fid, 0, new_size, {})
        next_local_fid += 1
        return next_local_fid-1
    else:
        return fid

def mynfs_read(virtual_fid, nofBytes):
    global fid_local_dictionary
    global cache_size

    if virtual_fid not in fid_local_dictionary:
        return (FileNotFoundErrorCode, 0)
    (fname, flags, fid, pos, old_size, cache) = fid_local_dictionary[virtual_fid]


    key = int(pos / CACHE_BLOCK_SIZE)

    RPCservicesWillBeNeeded = True
    if key in cache:
        new_size = old_size

        if time.time() - cache[key][1] > CACHE_BLOCK_FRESHNESS:
            print(RED, "Cache does not contain a fresh copy of this block!", ENDC)
            RPCservicesWillBeNeeded = True
        else:
            RPCservicesWillBeNeeded = False

    if RPCservicesWillBeNeeded:
        while True:
            (nofBytes_rtrned, bytes_read, new_pos, new_size) = readRPC(fid, key)
            if nofBytes_rtrned == FileNotFoundErrorCode:
                del fid_local_dictionary[virtual_fid]
                f = mynfs_open(fname, flags & 1110111111) # call my_open
                if f == FileExistsErrorCode:
                    print("File already exists...")
                    exit()
                elif f == FileNotFoundErrorCode:
                    print("File does not exist...")
                    exit()
            else:
                break

        # update cache
        if cache_size + CACHE_BLOCK_SIZE > CACHE_TOTAL_SIZE:
            print(RED, "Cache limits are reached.", ENDC)
            for file in fid_local_dictionary:
                (_, _, _, _, _, cache_to_delete_from) = fid_local_dictionary[file]
                if cache_to_delete_from:
                    del cache_to_delete_from[random.choice(list(cache_to_delete_from))]
                    cache_size -= CACHE_BLOCK_SIZE
                    break

        if key in cache:
            cache_size -= CACHE_BLOCK_SIZE

        cache[key] = (bytes_read.decode(), time.time())
        cache_size += CACHE_BLOCK_SIZE

    bytes_to_return = cache[key][0][pos % CACHE_BLOCK_SIZE:pos % CACHE_BLOCK_SIZE + nofBytes]

    fid_local_dictionary[virtual_fid] = (fname, flags, fid, pos + len(bytes_to_return), new_size, cache)
    return (len(bytes_to_return), bytes_to_return)

def mynfs_write(virtual_fid, buf):
    global fid_local_dictionary
    global cache_size

    if virtual_fid not in fid_local_dictionary:
        return FileNotFoundErrorCode
    (fname, flags, fid, pos, _, cache) = fid_local_dictionary[virtual_fid]

    if flags & 3 == 0:
        return PermissionDeniedErrorCode
    original_buf = buf
    while True:
        (bytes_written, new_pos, new_size) = writeRPC(fid, pos, buf)
        if bytes_written == FileNotFoundErrorCode:
            del fid_local_dictionary[virtual_fid]
            f = mynfs_open(fname, flags & 1110111111)
            if f == FileExistsErrorCode:
                print("File already exists...")
                exit()
            elif f == FileNotFoundErrorCode:
                print("File does not exist...")
                exit()
        else:
            break

    for key in range(int(pos / CACHE_BLOCK_SIZE), int(new_pos / CACHE_BLOCK_SIZE) + 1):
        if key in cache:
            cache_size -= CACHE_BLOCK_SIZE
            del cache[key]

    fid_local_dictionary[virtual_fid] = (fname, flags, fid, new_pos, new_size, cache)
    return bytes_written

def mynfs_seek(virtual_fid, pos, whence):
    global fid_local_dictionary

    if virtual_fid not in fid_local_dictionary:
        return FileNotFoundErrorCode
    (fname, flags, fid, old_pos, size, cache) = fid_local_dictionary[virtual_fid]
    # to set it to the position that the app sees (in case SEEK_CUR is set)
    if whence == SEEK_SET:
        start_pos = 0
    elif whence == SEEK_END:
        start_pos = size
    elif whence == SEEK_CUR:
        start_pos = old_pos
    else:
        return WrongWhenceCode

    fid_local_dictionary[virtual_fid] = (fname, flags, fid, start_pos + pos, size, cache)
    return start_pos + pos

def mynfs_close(virtual_fid):
    global cache_size
    global fid_local_dictionary

    if virtual_fid not in fid_local_dictionary:
        return FileNotFoundErrorCode
    (_, _, _,  _, _,cache) = fid_local_dictionary[virtual_fid]
    for key in cache:
        cache_size -= CACHE_BLOCK_SIZE
    del fid_local_dictionary[virtual_fid]
    return 0

def mynfs_set_cache(size, validity):
    CACHE_TOTAL_SIZE = size
    CACHE_BLOCK_FRESHNESS = validity

################### THREADS FOR MESSAGE SENDING/RECEIVING ######################
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
            else:
                print(RED, "DIPLOTYPO", ENDC)

            recv_buf_lock.release()
            send_buf_lock.acquire()
            if reqID in send_buf.keys():
                del send_buf[reqID]
            send_buf_lock.release()

################################################################################

if (len(sys.argv) != 3):
    print("args: server IP, server port")
SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# init sender and receiver thread
senderthread = Sender()
receiverthread = Receiver()
senderthread.daemon = True
receiverthread.daemon = True
senderthread.start()
receiverthread.start()
