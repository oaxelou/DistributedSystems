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

send_buf = {}
send_buf_lock = Lock()

recv_buf = {}
recv_buf_lock = Lock()

class Sender(Thread):
    def run(self):
        global send_buf
        global SERVER_IP, SERVER_PORT

        while 1:
            time.sleep(1)
            if send_buf:
                send_buf_lock.acquire()
                # etsi ta stelnei kyklika i guess
                # GUESS AGAIN YOU FUCKING IDIOT

                # message = send_buf[0]
                # sock.sendto(str(message).encode(), (SERVER_IP, SERVER_PORT))
                # print("sent request:", message)

                for req in send_buf:
                    message = send_buf[req]
                    sock.sendto(str(message).encode(), (SERVER_IP, SERVER_PORT))
                    print("sent request: ", message)

                print(send_buf)
                # request will not be removed from send_buf
                # until receiver thread receives the corresponding reply
                # SOOOO Receiver thread has access to send_buf
                send_buf_lock.release()

        print("end of thread")

class Receiver(Thread):
    def run(self):
        global recv_buf

        while 1:
            d = sock.recvfrom(UDP_SIZE)
            data = d[0]
            # address is not needed: always expecting things from server
            # maybe check it is actually the server who sent sth
            (text, reqID, addr) = make_tuple(data.decode())
            reply = (text, reqID)

            print("received reply: ", reply)

            # recv_buf_lock.acquire()
            # recv_buf.append(reply)
            # for item in recv_buf:
            #     if reqID in item:
            #     # sbhse to apo to send_buf
            #         send_buf_lock.acquire()
            #         for item2 in send_buf:
            #             if reqID in item2:
            #                 send_buf.pop(item2)
            #                 break
            #         send_buf_lock.release()
            #         break
            # recv_buf_lock.release()

            recv_buf_lock.acquire()

            recv_buf[reqID] = reply
            send_buf_lock.acquire()
            if reqID in send_buf.keys():
                del send_buf[reqID]
            send_buf_lock.release()

            recv_buf_lock.release()


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
sock.bind(('', 2000))


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
