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
RESEND_TIMEOUT = 0.01

send_buf = {}
send_buf_lock = Lock()

recv_buf = {}
recv_buf_lock = Lock()

class Sender(Thread):
    def run(self):
        global send_buf
        global SERVER_IP, SERVER_PORT

        while 1:
            if send_buf:
                send_buf_lock.acquire()

                for req in send_buf:
                    message = send_buf[req]
                    sock.sendto(str(message).encode(), (SERVER_IP, SERVER_PORT))
                    print("sent request: ", message)

                # request will not be removed from send_buf
                # until receiver thread receives the corresponding reply
                # SOOOO Receiver thread has access to send_buf
                send_buf_lock.release()
                time.sleep(RESEND_TIMEOUT)


class Receiver(Thread):
    def run(self):
        global recv_buf

        while 1:
            d = sock.recvfrom(UDP_SIZE)
            data = d[0]
            # address is not needed: always expecting things from server
            # maybe check it is actually the server who sent sth

            recv_buf_lock.acquire()

            (text, reqID, addr) = make_tuple(data.decode())
            reply = (text, reqID)
            if reqID not in recv_buf.keys():
                recv_buf[reqID] = reply
                print("received reply: ", reply)

            send_buf_lock.acquire()
            if reqID in send_buf.keys():
                del send_buf[reqID]

            send_buf_lock.release()
            recv_buf_lock.release()

#######################    CLIENT PORT FUNCTION   ##########################

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

MY_PORT = find_avl_port(sock, '')
# sock.bind(('', MY_PORT))


reqID = -1

# put messages in send_buffer
for i in range (10):
    if i % 2 == 0:
        text = "hello i am " + str(i)
    else:
        text = "my name is " + str(i)
    reqID += 1

    # i'm gonna leave that here as is, in case we need the message
    # to be a tuple
    message = (text, reqID)
    send_buf_lock.acquire()
    send_buf[reqID] = message
    send_buf_lock.release()

# print(send_buf)

# init sender and receiver thread
senderthread = Sender()
receiverthread = Receiver()
senderthread.daemon = True
receiverthread.daemon = True
senderthread.start()
receiverthread.start()

while 1:
    pass
