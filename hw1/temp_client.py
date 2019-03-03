import socket
import time
import random
import threading
from threading import Thread
from threading import Lock
import fcntl, os
import errno


MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000
SERVICEID = 1

PERIOD = 2

lock = Lock()
requests2send = {}
end_lifetime = 0

################################################################################
# client sender thread code
class AtMostOnceSender(Thread):
    def run(self):
        while 1:
            time.sleep(PERIOD)
            if end_lifetime == 1:
                print("Exiting from snder thread")
                break
            lock.acquire()
            print("Printing list of requests to send", requests2send)
            for request in requests2send.keys():
                print("Going to send request", request)
                sock.sendto(str(requests2send[request]).encode(), (MCAST_GRP, MCAST_PORT))
            lock.release()
################################ APP FUNCTIONS #################################
def app():

    block = 0

    while 1:
        try:
            int2check = input("int2check: ")
            # int2check = file_input[i]

        except KeyboardInterrupt:
            sock.close()
            end_lifetime = 1
            print("Ending communication...")
            exit()

        if not int2check:
            sock.close()
            end_lifetime = 1
            print("Ending communication...")
            exit()

        requestID = sendRequest(SERVICEID, int2check)
        # while getReply(requestID, block) == 1:
        #     time.sleep(1)
        #     print("will retry to get")
        # time.sleep(1)
        getReply(requestID, block)

def sendRequest(svcid, int2check):
    # sendRequest.__dict__.setdefault('atMostOnceThread', -1)
    #
    # if sendRequest.atMostOnceThread == -1:
    #     sendRequest.atMostOnceThread = AtMostOnceSender()
    #     sendRequest.atMostOnceThread.start()

    sendRequest.__dict__.setdefault('requestID', -1)
    sendRequest.requestID += 1


    # probably won't be needed (99%)
    try:
        message2send = (svcid, sendRequest.requestID, int(int2check))
    except ValueError as verror:
        message2send = (svcid, sendRequest.requestID, int2check)

    lock.acquire()
    print("Adding to requests2send: ", message2send)
    requests2send[sendRequest.requestID] = message2send
    lock.release()
    # print("added ",message2send)
    return sendRequest.requestID

def getReply(requestID, block):
    print("Going to wait")
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        end_lifetime = 1
        atMostOnceThread.join()
        sock.close()
        print("Ending temp client/slave-server")
        exit()
    except socket.error as e:
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            print("there is no reply and getReply is nonBlocking")
            return 1
        else:
            print("serious error", e)
            return 2

    data = d[0]
    addr = d[1]

    print("Message[" + addr[0] + ":" + str(addr[1]) + "] : " + data.decode().strip())

    lock.acquire()
    if requestID in requests2send:
        print(requestID, "has been received and will be removed from list")
        requests2send.pop(requestID)
    else:
        print("Request ", requestID   , " not found")
    print(requests2send)
    lock.release()
    return 0

############################### SOCKET CREATION ################################

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)

print("Socket is ready")

################################################################################
atMostOnceThread = -1
atMostOnceThread = AtMostOnceSender()
atMostOnceThread.start()
app()
