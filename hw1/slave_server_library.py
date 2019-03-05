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

PERIOD = 5

################################################################################
# slave-server checker thread code
class PingSender(Thread):
    def run(self):
        while 1:
            try:
                time.sleep(PERIOD)
            except KeyboardInterrupt:
                print("ping sender caught an ^C")
                break

            # print("Going to send ping")
            try:
                sock.sendto(str(((0,0), 0, "ping")).encode(), (MCAST_GRP, MCAST_PORT))
            except OSError:
                print("Master thread deleted socket")
                break

############################ LIBRARY FUNCTIONS #################################
def register(svcid):
    sock.sendto(str((svcid, 0, "ADD_SERVER")).encode(), (MCAST_GRP, MCAST_PORT))

###################################################
def unregister(svcid):
    sock.sendto(str((svcid, 0, "RMV_SERVER")).encode(), (MCAST_GRP, MCAST_PORT))

###################################################
def getRequest(svcid):
    print("Going to wait for a job")
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        unregister(svcid)
        sock.close()
        # elegxos gia to thread??
        print("Slave is going to wait for the thread to quit")
        pingthread.join()
        print("All good. Slave quiting...")
        # print("Ending temp slave-server")
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
    # sock.sendto(str((SERVICEID, (client[0], client[1], reqID), message2send)).encode(), (MCAST_GRP, MCAST_PORT))
    sock.sendto(str((client, reqID, reply)).encode(), (MCAST_GRP, MCAST_PORT))
    # print("Sent ", reply)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

pingthread = PingSender()
pingthread.start()
