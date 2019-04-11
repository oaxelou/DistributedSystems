import socket
import time
import struct
from ast import literal_eval as make_tuple
import threading
from threading import Thread
from threading import Lock
import sys
import random

UDP_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_buf = []
recv_buf_lock = Lock()
send_buf = []
send_buf_lock = Lock()


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

            (text, reqID) = make_tuple(data.decode())
            req = (text, reqID, addr)
            recv_buf_lock.acquire()
            recv_buf.append(req)
            recv_buf_lock.release()
            # print(recv_buf)

############################    SENDER THREAD   ################################

class Sender(Thread):
    def run(self):
        global send_buf
        global sock

        # always try to receive stuff
        while 1:
            if send_buf:
                send_buf_lock.acquire()
                msg2send = send_buf[0]
                addr = msg2send[2]

                sock.sendto(str(msg2send).encode(), (addr))

                send_buf.pop(0)
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
        recv_buf_lock.acquire()
        msg2send = recv_buf[0]

        text = msg2send[0]
        reqID = msg2send[1]
        addr = msg2send[2]
        # compute
        if "hello" in text:
            reply_text = "hi"
        else:
            reply_text = "nice"

        recv_buf.pop(0)
        recv_buf_lock.release()

        # construct reply tuple/msg
        reply = (reply_text, reqID, addr)
        send_buf_lock.acquire()
        send_buf.append(reply)
        send_buf_lock.release()
