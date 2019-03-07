# slave server library file.
#
#


import socket
from ast import literal_eval as make_tuple

import time
import threading
from threading import Thread
from  threading import Lock

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10300

PERIOD = 0.5
serviceID = -1
################################################################################
# slave-server checker thread code
class PingSender(Thread):
    def run(self):
        while 1:
            time.sleep(PERIOD)
            sock.sendto(str(((0,0), 0, (serviceID, "ping"))).encode(), (MCAST_GRP, MCAST_PORT))

############################ LIBRARY FUNCTIONS #################################
def register(svcid):
    global serviceID
    serviceID = svcid
    sock.sendto(str((svcid, 0, (svcid, "ADD_SERVER"))).encode(), (MCAST_GRP, MCAST_PORT))

###################################################
def unregister(svcid):
    sock.sendto(str((svcid, 0, (svcid, "RMV_SERVER"))).encode(), (MCAST_GRP, MCAST_PORT))

###################################################
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
        return ((0,0), 0 , 0)

    return (client, reqID, message)

###################################################
def sendReply(client, reqID, reply):
    print("Going to sendto ", client)
    sock.sendto(str((client, reqID, reply)).encode(), (MCAST_GRP, MCAST_PORT))


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

pingthread = PingSender()
pingthread.daemon = True
pingthread.start()
