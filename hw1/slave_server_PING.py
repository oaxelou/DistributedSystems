import socket
from ast import literal_eval as make_tuple

import time
import threading
from threading import Thread
from  threading import Lock

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000
SERVICEID = 1

PERIOD = 5

################################################################################
# slave-server checker thread code
class PingSender(Thread):
    def run(self):
        while 1:
            time.sleep(PERIOD)
            print("Going to send ping")
            sock.sendto(str(((0,0), 0, "ping")).encode(), (MCAST_GRP, MCAST_PORT))


################################################################################
def isprime(x):
    for i in range(2, x-1):
        if x % i == 0:
            return False
    return True


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

sock_ping = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock_ping.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

print("Socket is ready")

pingthread = PingSender()
pingthread.start()

# inform master that I exist and am connected - probably register()
sock.sendto(str((SERVICEID, 0, "ADD_SERVER")).encode(), (MCAST_GRP, MCAST_PORT))

while 1:
    print("Going to wait for a job")
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        print("Ending temp slave-server")
        break

    data = d[0]
    addr = d[1]
    print("Received ", data.decode())
    print("from ", addr)

    try:
        (client, reqID, message) = make_tuple(data.decode())
    except ValueError as verror:
        print("Received message with", verror)
        print("Going to ignore it...")
        continue
    print("reached here")
    if message == "ping":
        print("SLAVE SERVER IS HERE! DON'T KILL ME")
        sock.sendto(("pong").encode(), addr)
    else:
        message2send = "ack - " + str(message) + " is" + (" not " if not isprime(int(message)) else " ") + "prime"

        print("Going to sendto ", addr)
        sock.sendto(str((client, reqID, message2send)).encode(), (MCAST_GRP, MCAST_PORT))
        print("Sent ",message2send)

sock.close()
print("Slave is going to wait for the thread to quit")
pingthread.join()
print("All good. Slave quiting...")
