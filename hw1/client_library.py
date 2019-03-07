# Distributed Systems - hw1 :
# Asychronous request-reply with at most once and dynamic management of the servers
#                                                        (load balancing)
# Axelou Olympia 2161
# Tsitsopoulou Irene 2203
#
# client_library.py: Client middleware file
#

import socket
from ast import literal_eval as make_tuple
import time
import random
import threading
from threading import Thread
from threading import Lock
import errno

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10300

PERIOD = 1
MAX_ATTEMPTS = 50
RECEIVED_FLAG = -5

SUCCESS = 0
NOT_YET_ERROR = 1
EXPIRED_ERROR = 2
NO_SERVER_ERROR = 3
############################### client sender thread #################################
# It periodically resends every request in requests2send with attempts flag > 0 (max attempts = MAX_ATTEMPTS)
# until the receiver of the client has taken the reply
class AtMostOnceSender(Thread):
    def run(self):
        global sock
        while 1:
            time.sleep(PERIOD)
            lock.acquire()
            lock_received.acquire()
            for request in list(requests2send.keys()):
                if (request not in requestsReceived.keys()):
                    (message, attempts) = requests2send[request]
                    if attempts > 0:
                        requests2send[request] = (message, attempts - 1)
                        sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))
                    elif attempts == RECEIVED_FLAG:
                        print("I have received this request: ", message, "Going to ignore it...")
                    else:
                        print("max attempts expired. going to remove it from sending list")
                        del requests2send[request]
            lock.release()
            lock_received.release()

############################## client receiver thread ################################
# It blocks until a message is received. It adds it in the requestsReceived dictionary
# and informs the requests2send dictionary with the RECEIVED_FLAG in attempts
class AtMostOnceReceiver(Thread):
    global sock
    def run(self):
        while 1:
            try:
                d = sock.recvfrom(1024)
            except KeyboardInterrupt:
                print("\tEnding temp client")
                break
            except OSError:
                print("\tapp terminating this thread")
                break

            (reqID, message) = make_tuple(d[0].decode())
            if message == "NO-SERVER":
                print("There is no slave-server available")

            lock_received.acquire()
            requestsReceived[reqID] = message
            lock_received.release()

            lock.acquire()
            if reqID in requests2send:
                (int2send, _) = requests2send[reqID]
                requests2send[reqID] = (int2send, RECEIVED_FLAG)
            lock.release()

################################################################################
# Forms the message to send and adds the request in the request2send dictionary
# and returns the requestID
def sendRequest(svcid, int2check):
    sendRequest.__dict__.setdefault('requestID', -1)
    sendRequest.requestID += 1
    try:
        message2send = (svcid, sendRequest.requestID, int(int2check))
    except ValueError as verror:
        message2send = (svcid, sendRequest.requestID, int2check)

    lock.acquire()
    requests2send[sendRequest.requestID] = (message2send, MAX_ATTEMPTS)
    lock.release()
    return sendRequest.requestID

################################################################################
# 2nd parameter sets the communication to blocking or non-blocking
# Return value:
# SUCCESS = 0
# NOT_YET_ERROR = 1 (only for non-blocking)
# EXPIRED_ERROR = 2 (request in received dictionary but not in to-send dictionary)
# NO_SERVER_ERROR = 3 (no servers available for this requestID)
def getReply(requestID, block):

    lock.acquire()
    if requestID in requests2send:
        lock.release()
    else:
        print(requestID, "not found in outgoing requests. So, I'm going to ignore it")
        lock.release()
        return (EXPIRED_ERROR, False)

    if block: # if blocking argument is checked
        lock_received.acquire()
        # it's going to be blocked in the while until it has the reply
        while requestID not in requestsReceived:
            lock_received.release()
            lock.acquire()
            # The request has expired and it's going to be ignored
            if requestID not in requests2send:
                print(requestID, "not found in outgoing requests. So, I'm going to ignore it")
                lock.release()
                return (EXPIRED_ERROR, False)
            lock.release()
            # The reply is not yet delivered. It's going to sleep for 0.1sec and try again
            time.sleep(0.1)
            lock_received.acquire()

        returnValue = requestsReceived[requestID]
        del requestsReceived[requestID]
        lock_received.release()
        lock.acquire()
        del requests2send[requestID]
        lock.release()
        if returnValue == "NO-SERVER":
            # no slave server available (message sent by the master server)
            return (NO_SERVER_ERROR, False)
        return (SUCCESS, returnValue)
    else:
        lock_received.acquire()

        if requestID in requestsReceived:
            returnValue = requestsReceived[requestID]
            requestsReceived.pop(requestID)
            lock_received.release()
            lock.acquire()
            requests2send.pop(requestID)
            lock.release()
            if returnValue == "NO-SERVER":
                return (NO_SERVER_ERROR, False)
            return (SUCCESS, returnValue)
        else:
            lock_received.release()
            return (NOT_YET_ERROR, False)




############################### SOCKET CREATION ################################
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

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
