import socket
from ast import literal_eval as make_tuple
import time
import random
import threading
from threading import Thread
from threading import Lock
# import fcntl, os
import errno


MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000
SERVICEID = 1

PERIOD = 1

lock = Lock()
lock_received = Lock()
requests2send = {}
requestsReceived = {}
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
            lock_received.acquire()
            # print("Printing list of requests to send", requests2send)
            for request in requests2send.keys():
                if request not in requestsReceived.keys():
                    # print("Going to send request", request)
                    sock.sendto(str(requests2send[request]).encode(), (MCAST_GRP, MCAST_PORT))
            lock.release()
            lock_received.release()
################################################################################

# client sender thread code
class AtMostOnceReceiver(Thread):
    def run(self):
        while 1:
            if end_lifetime == 1:
                print("Exiting from snder thread")
                break
            # print("Going to sleep")
            try:
                d = sock.recvfrom(1024)
            except KeyboardInterrupt:
                print("Ending temp client")
                break

            # print("--------------------Message[" + d[1][0] + ":" + str(d[1][1]) + "] : " + d[0].decode().strip())
            (reqID, message) = make_tuple(d[0].decode())
            lock_received.acquire()
            # print("Adding message that I received in requestsReceived")
            requestsReceived[reqID] = message
            # print("requestsReceived:", requestsReceived)
            # print(requestsReceived)
            lock_received.release()
################################ APP FUNCTION ##################################
def app():

    block = 1
    req2wait4 = {}

    # while 1:
    print(" ")
    print(" ")
    print(" ")
    print(" ")
    print(" ")
    print(" ")
    print(" ")
    print(" ")

    for i in range(10):
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
        req2wait4[requestID] = int2check

    # while req2wait4:
    for req in list(req2wait4.keys()):
        if getReply(req, block) == 0:
            # print(" ")
            # print(" ")
            # print("Removing ", req, "from requests to wait for")
            del req2wait4[req]
        else:
            print(" ")
                # print(" ")
                # print("Nothing yet for ", req)
                # time.sleep(2)
        # while getReply(requestID, block) == 1:
        #     time.sleep(1)
        #     print("will retry to get")
        # time.sleep(2)
        # print("")
        # print("")
        # print("Going to wait for reply")
        # print("")
        # for i in range(10):
        #     getReply(i, block)

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
    # print("Adding to requests2send: ", message2send)
    requests2send[sendRequest.requestID] = message2send
    lock.release()
    # print("added ",message2send)
    return sendRequest.requestID

def getReply(requestID, block):
    if block:
        lock_received.acquire()
        while requestID not in requestsReceived:
            lock_received.release()
            # print("Request ", requestID   , " not found in incoming requests")
            print(requestsReceived)
            # print()
            time.sleep(1)
            lock_received.acquire()

        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Message: ", requestsReceived[requestID])
        # print(requestID, "has been received and will be removed from received packages")
        requestsReceived.pop(requestID)
        # print(requestsReceived)
        lock_received.release()
    else:
        lock_received.acquire()
        if requestID in requestsReceived:
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Message: ", requestsReceived[requestID])
            # print(requestID, "has been received and will be removed from received packages")
            requestsReceived.pop(requestID)
            # print(requestsReceived)
            lock_received.release()
        else:
            # print("Request ", requestID   , " not found in incoming requests")
            # print(requestsReceived)
            lock_received.release()
            return 1
    # telos diaxwrismou blocking - non blocking

    lock.acquire()
    if requestID in requests2send:
        # print(requestID, "has been found in outgoing requests")
        requests2send.pop(requestID)
    # else:
        # print(requestID, "not found in outgoing requests")
    print(requests2send)
    lock.release()
    return 0

############################### SOCKET CREATION ################################

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

# fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)

print("Socket is ready")

################################################################################
# atMostOnceThread = -1
atMostOnceThread = AtMostOnceSender()
atMostOnceThread.start()

receiverThread = AtMostOnceReceiver()
receiverThread.start()

app()
