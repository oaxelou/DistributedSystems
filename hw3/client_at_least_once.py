import socket
import time
import struct
from ast import literal_eval as make_tuple
import threading
from threading import Thread
from threading import Lock
import sys
import random

send_buf = []
send_buf_lock = Lock()

class Sender(Thread):
    def run(self):
        global send_buf
        global SERVER_IP, SERVER_PORT

        while 1:
            if send_buf:
                send_buf_lock.acquire()
                message = send_buf[item]
                # resend until ?????
                sock.sendto(str(message).encode(), (SERVER_IP, SERVER_PORT))
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
sock.bind('')

# init sender thread
senderthread = Sender()
senderthread.daemon = True
senderthread.start()

reqID = 0

# put messages in send_buffer
for i in range (10):
    if i % 2 == 0:
        text = "hello i am" + i
    else:
        text = "my name is" + i
    reqID += 1
    message = (text, reqID)
    send_buf.append(msg)

# wait to receive all replies
while send_buf:
    data = sock.recvfrom(1024)
