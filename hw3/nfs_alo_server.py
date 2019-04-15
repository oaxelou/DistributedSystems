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
arithmos_proteraiothtas = 0
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

def my_seek(fid, pos, whence):
    try:
        current_pos = os.lseek(fid, pos, whence)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        exit()
    return current_pos

def my_read(fid, pos, nofBytes):
    current_pos = my_seek(fid, pos, SEEK_SET)
    print("current position: ", current_pos)
    if current_pos == BadFileDescriptorCode or current_pos == None:
        print("Bad file descriptor (seek). Going to terminate...")
        exit()
    try:
        bytesRead = os.read(fid, nofBytes)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return None
    return bytesRead  # decode()

def my_write(fid, pos, buf):
    current_pos = my_seek(fid, pos, SEEK_SET)
    print("current position: ", current_pos)
    if current_pos == BadFileDescriptorCode:
        print("Bad file descriptor (seek). Going to terminate...")
        exit()
    try:
        bytesWritten = os.write(fid, buf.encode())
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return BadFileDescriptorCode
    return bytesWritten
############################### END OF NFS STUFF ###############################

###########################    RECEIVER THREAD   ###############################

class Receiver(Thread):
    def run(self):
        global recv_buf
        global sock
        global arithmos_proteraiothtas

        # always try to receive stuff
        while 1:
            d = sock.recvfrom(UDP_SIZE)
            data = d[0]
            addr = d[1]

            (serviceType, args, reqID) = make_tuple(data.decode())
            req = (serviceType, args, reqID, addr) #                                     vale to serviceType sthn arxh tou tuple (kai allakse kai ston kwdika to pws diaxeirizetai to tuple)

            recv_buf_lock.acquire()
            recv_buf[arithmos_proteraiothtas] = req
            print("received:", recv_buf[arithmos_proteraiothtas])
            arithmos_proteraiothtas += 1
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
                (fid, reqID,addr) = reply2send
                reply2send = (fid, reqID)
                print(GREEN, "going to send reply: ", reply2send, ENDC)

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

# Open server logfile
if (len(sys.argv) == 2) and (sys.argv[1] == "old_session"):
    logfile_mode = O_CREAT | O_RDWR
    logfile_fid = my_open("server_logfile.log", logfile_mode)
    print("Opened logfile with flags: ", logfile_mode)
    size = my_seek(logfile_fid, 0, SEEK_END)
    fid_dictionary_str = my_read(logfile_fid, 0, size)
    fid_dictionary = eval(fid_dictionary_str)
    os.close(logfile_fid)
    for virtual_fid_key in fid_dictionary.keys():
        fid, fname, f_mode, f_timestamp = fid_dictionary[virtual_fid_key]
        fid = my_open(fname, f_mode)
        fid_dictionary[virtual_fid_key] = (fid, fname, f_mode, f_timestamp)
print("Initial fid_dictionary: ", fid_dictionary)

time.sleep(4)

# init sender and receiver thread
senderthread = Sender()
receiverthread = Receiver()
senderthread.daemon = True
receiverthread.daemon = True
senderthread.start()
receiverthread.start()


while 1:
    recv_buf_lock.acquire()
    if recv_buf:
        #  take a request from recv_buf (the one with the smaller reqID),
        #  process it and delete it from buffer

        # Find min arithmo proteraiothtas
        min_arithmos_proter = random.choice(list(recv_buf.keys()))
        for arithm_prot_key in recv_buf:
            if arithm_prot_key < min_arithmos_proter:
                min_arithmos_proter = arithm_prot_key

        msg2proccess = recv_buf[min_arithmos_proter]
        print("going for req:", min_arithmos_proter)
        print("main thread: going to process:", min_arithmos_proter,":", msg2proccess)

        serviceType = msg2proccess[0]
        args = msg2proccess[1]
        reqID = msg2proccess[2]
        addr = msg2proccess[3]

        # compute
        if serviceType == "open":
            fileAlreadyOpened = False
            fname = args[0]
            flags = args[1]
            # gia kathe entry sto dictionary tsekare to deutero pedio tou tuple
            for virtual_fid_key in fid_dictionary.keys():
                fid, fname_value, _, _ = fid_dictionary[virtual_fid_key]
                if fname == fname_value:
                    if flags == O_CREAT | O_EXCL:
                        reply_data = (FileExistsErrorCode, 0)
                        fileAlreadyOpened = True
                        # put in buffer & continue?
                    else: # file already exists
                        reply_data = (virtual_fid_key, my_seek(fid, 0, SEEK_END))
                        fileAlreadyOpened = True
                        # put in buffer & continue?

            if fileAlreadyOpened == False: # open new file
                f = my_open(fname, O_CREAT | O_RDWR) # call my_open
                if f == FileExistsErrorCode:
                    print("File already exists...")
                    exit()
                elif f == FileNotFoundErrorCode:
                    print("File does not exist...")
                    exit()

                fid_dictionary[next_fid] = (f, fname, flags, 0)

                # anoigoume me O_TRUNC
                logfile_fid = my_open("server_logfile.log", O_CREAT | O_TRUNC | O_RDWR)
                print("Reopened logfile with O_TRUNC")
                my_write(logfile_fid, 0, str(fid_dictionary))

                next_fid += 1
                print(RED, fid_dictionary, ENDC)
                reply_data = (next_fid-1, my_seek(f, 0, SEEK_END))

        elif serviceType == "read":
            virtual_fid = args[0]
            pos = args[1]
            nofBytes = args[2]
            if virtual_fid not in fid_dictionary.keys():
                reply_data = (FileNotFoundErrorCode, 0, 0, 0)
            else:
                fid, _, _, _ = fid_dictionary[virtual_fid]
                try:
                    bytesRead = my_read(fid, pos, nofBytes)
                    reply_data = (len(bytesRead), bytesRead, my_seek(fid, 0, SEEK_CUR), my_seek(fid, 0, SEEK_END))
                except OSError:
                    print("Bad file descriptor. Terminating program...")
                    reply_data = (BadFileDescriptorCode, 0, 0, 0)


        elif serviceType == "write":
            virtual_fid = args[0]
            pos = args[1]
            write_buf = args[2]
            if virtual_fid not in fid_dictionary.keys():
                reply_data = (FileNotFoundErrorCode, 0, 0)
            else:
                fid, _, _, _ = fid_dictionary[virtual_fid]
                try:
                    bytes_written = my_write(fid, pos, write_buf)
                    reply_data = (bytes_written, my_seek(fid, 0, SEEK_CUR), my_seek(fid, 0, SEEK_END))
                except OSError:
                    print("Bad file descriptor. Terminating program...")
                    reply_data = (BadFileDescriptorCode, 0, 0)


        else:
            reply_data = "I don't know what you are talking about. Are you talking to me?"
        del recv_buf[min_arithmos_proter]
        recv_buf_lock.release()

        # construct reply tuple/msg and add to send_buf

        reply = (reply_data, reqID, addr)

        # sender thread will take care of it
        send_buf_lock.acquire()
        send_buf[min_arithmos_proter] = reply #                      ISWS APLA NA TO ESTELNE (diladi na mhn uparxei sender thread)
        send_buf_lock.release()
    else:
        recv_buf_lock.release()
