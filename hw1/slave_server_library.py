# Distributed Systems - hw1 :
# Asychronous request-reply with at most once and dynamic management of the servers
#                                                        (load balancing)
# Axelou Olympia 2161
# Tsitsopoulou Irene 2203
#
# slave_server_library.py: Slave server middleware file
#

import time
import socket
import threading
from  threading import Lock
from threading import Thread
from ast import literal_eval as make_tuple

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10300

PERIOD = 0.5
serviceID = -1

ERROR_INVALID_FORMAT = ((0,0), 0, 0)
ERROR_INVALID_SERVICEID = ((0,0), 0, 1)

########################### slave-server checker thread code #########################
# It sends periodically "ping" so that the master server knows that it exists
class PingSender(Thread):
    def run(self):
        while 1:
            time.sleep(PERIOD)
            sock.sendto(str(((0,0), 0, (serviceID, "ping"))).encode(), (MCAST_GRP, MCAST_PORT))


################################ LIBRARY FUNCTIONS ###################################
# Sends "ADD_SERVER" to master to register. Doesn't expect ACK but the master server
# Informs him in getRequest if something is wrong (eg Not valid svcid)
def register(svcid):
    global serviceID
    serviceID = svcid
    sock.sendto(str((svcid, 0, (svcid, "ADD_SERVER"))).encode(), (MCAST_GRP, MCAST_PORT))

###################################################
# Sends "RMV_SERVER" to master to register. Doesn't expect ACK but the master server
def unregister(svcid):
    sock.sendto(str((svcid, 0, (svcid, "RMV_SERVER"))).encode(), (MCAST_GRP, MCAST_PORT))

###################################################
# Bloks until he receives a request.
# This function returns a tuple with :
#  if success : (client<IP,port>, requestID, message)
#  if invalid svcid : ERROR_INVALID_SERVICEID = ((0,0), 0, 1)
#  if invalid message format : ERROR_INVALID_FORMAT = ((0,0), 0, 0)
def getRequest(svcid):
    print("Going to wait for a job")
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        unregister(svcid)
        sock.close()
        print("All good. Slave quiting...")
        exit()

    data = d[0]
    addr = d[1]
    print("Received ", data.decode())

    try:
        (client, reqID, message) = make_tuple(data.decode())
    except ValueError as verror:
        print("Received message with", verror)
        print("Going to ignore it...")
        return ERROR_INVALID_FORMAT

    if message == "WRONG-SERVICEID":
        return ERROR_INVALID_SERVICEID
    return (client, reqID, message)

###################################################
# It sends reply. It doesn't return anything
def sendReply(client, reqID, reply):
    print("Going to sendto ", client)
    sock.sendto(str((client, reqID, reply)).encode(), (MCAST_GRP, MCAST_PORT))


# Initialize socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

# Initialize ping sender thread
pingthread = PingSender()
pingthread.daemon = True
pingthread.start()
