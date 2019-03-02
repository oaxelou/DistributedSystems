import socket
from ast import literal_eval as make_tuple

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000
SERVICEID = 1

def isprime(x):
    for i in range(2, x-1):
        if x % i == 0:
            return False
    return True


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)


print("Socket is ready")

# inform master that I exist and am connected - probably register()
sock.sendto(str((SERVICEID, 0, "ADD_SERVER")).encode(), (MCAST_GRP, MCAST_PORT))
print("Going to wait for ack")
try:
    d = sock.recvfrom(1024)
except KeyboardInterrupt:
    print("Ending temp slave-server")
    exit()

print("Received ", d[0].decode())

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

    try:
        (client, reqID, message) = make_tuple(data.decode())
    except ValueError as verror:
        print("Received message with", verror)
        print("Going to ignore it...")
        continue

    message2send = "ack - " + str(message) + " is" + (" not " if not isprime(message) else " ") + "prime"

    print("Going to sendto ", addr)
    sock.sendto(str((SERVICEID, (client[0], client[1], reqID), message2send)).encode(), (MCAST_GRP, MCAST_PORT))
    print("Sent ",message2send)

sock.close()
