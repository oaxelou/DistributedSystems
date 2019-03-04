import socket
from ast import literal_eval as make_tuple

import time
import threading
from threading import Thread
from  threading import Lock

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000
SERVICEID = 1

run_thread = 1

PERIOD = 5

################################################################################
# slave-server checker thread code
class PingSender(Thread):
    def run(self):
        while (run_thread):
            time.sleep(PERIOD)
            print("Going to send ping")
            try:
                sock.sendto(str(((0,0), 0, "ping")).encode(), (MCAST_GRP, MCAST_PORT))
            # edw mou petaei exception: OSError: [Errno 9] Bad file descriptor
            # epeidh ginetai sock.close
            except OSError:
                break

            # sock.sendto(str(((0,0), 0, "ping")).encode(), (MCAST_GRP, MCAST_PORT))

############################### APP  FUNCTION ##################################
def isprime(x):
    for i in range(2, x-1):
        if x % i == 0:
            return False
    return True

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
        unregister(SERVICEID)
        run_thread = 0
        print("Slave is going to wait for the thread to quit")
        sock.close()
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


################################################################################
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

pingthread = PingSender()
pingthread.start()

register(SERVICEID)
while 1:
    (client, reqID, message) = getRequest(SERVICEID)
    if((client, reqID, message) == ((0,0), 0, 0)):
        continue
    message2send = str(isprime(int(message)))
    sendReply(client, reqID, message2send)

# sock.close()
# print("Slave is going to wait for the thread to quit")
# pingthread.join()
# print("All good. Slave quiting...")
