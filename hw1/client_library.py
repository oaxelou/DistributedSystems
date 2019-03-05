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
MCAST_PORT = 10300
SERVICEID = 1

PERIOD = 1
MAX_ATTEMPTS = 10

################################################################################
# client sender thread code
class AtMostOnceSender(Thread):
    def run(self):
        global sock
        # global end_lifetime
        while 1:
            # print("Going to sleep")
            time.sleep(PERIOD)
            # lock_lifetime.acquire()
            # print ( "end_lifetime", end_lifetime)
            # if end_lifetime == 1:
            #     lock_lifetime.release()
            #     print("Exiting from snder thread")
            #     break
            # lock_lifetime.release()

            lock.acquire()
            lock_received.acquire()
            # print("Printing list of requests to send", requests2send)
            for request in list(requests2send.keys()):
                if (request not in requestsReceived.keys()):
                    (message, attempts) = requests2send[request]
                    # print("message ", message)
                    # print("attempts ", attempts)
                    if attempts > 0:
                        # print("Going to send request", request)
                        # print("requests2send")
                        # print(requests2send)
                        requests2send[request] = (message, attempts - 1)
                        # requests2send[request][1] -= 1
                        sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))
                    else:
                        print("max attempts expired. going to reove it from sending list")
                        del requests2send[request]
            lock.release()
            lock_received.release()
################################################################################

# client sender thread code
class AtMostOnceReceiver(Thread):
    global sock
    def run(self):
        # global end_lifetime
        while 1:
            print("\tgoing to wait for an answer from server")
            try:
                d = sock.recvfrom(1024)
            except KeyboardInterrupt:
                print("\tEnding temp client")
                break
            except OSError:
                print("\tapp terminating this thread")
                break

            # print("\tgoing to the the lock in receiver")
            # lock_lifetime.acquire()
            # if end_lifetime == 1:
            #     lock_lifetime.release()
            #     print("\tExiting from receiver thread")
            #     break
            # lock_lifetime.release()

            print("--------------------Message[" + d[1][0] + ":" + str(d[1][1]) + "] : " + d[0].decode().strip())
            (reqID, message) = make_tuple(d[0].decode())
            if message == "There is no slave-server available":
                print("There is no slave-server available")
                continue
            lock_received.acquire()
            # print("Adding message that I received in requestsReceived")
            requestsReceived[reqID] = message
            # print("requestsReceived:", requestsReceived)
            # print(requestsReceived)
            lock_received.release()


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
    requests2send[sendRequest.requestID] = (message2send, MAX_ATTEMPTS)
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

        print("Received ", requestID, ": ", requestsReceived[requestID])
        # print(requestID, "has been received and will be removed from received packages")
        returnValue = requestsReceived[requestID]
        requestsReceived.pop(requestID)
        # print(requestsReceived)
        lock_received.release()
    else:
        lock_received.acquire()
        if requestID in requestsReceived:
            returnValue = requestsReceived[requestID]
            print("Received ", requestID, ": ", requestsReceived[requestID])
            # print(requestID, "has been received and will be removed from received packages")
            requestsReceived.pop(requestID)
            # print(requestsReceived)
            lock_received.release()
        else:
            # print("Request ", requestID   , " not found in incoming requests")
            # print(requestsReceived)
            lock_received.release()
            return (1, False)
    # telos diaxwrismou blocking - non blocking

    lock.acquire()
    if requestID in requests2send:
        # print(requestID, "has been found in outgoing requests")
        requests2send.pop(requestID)
    # else:
        # print(requestID, "not found in outgoing requests")
    print(requests2send)
    lock.release()
    return (0, returnValue)

############################### SOCKET CREATION ################################

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

print("Socket is ready")

################################################################################
atMostOnceThread = AtMostOnceSender()
atMostOnceThread.daemon = True
atMostOnceThread.start()

receiverThread = AtMostOnceReceiver()
receiverThread.daemon = True
receiverThread.start()

lock = Lock()
lock_received = Lock()
requests2send = {}
requestsReceived = {}
# lock_lifetime = Lock()

# end_lifetime = 0
