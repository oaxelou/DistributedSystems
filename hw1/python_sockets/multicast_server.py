import socket
import struct

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000

def isprime(x):
    for i in range(2, x-1):
        if x % i == 0:
            return False
    return True


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,socket.inet_aton(get_local_ip()))
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# mreq = socket.inet_aton(MCAST_GRP) + str(socket.INADDR_ANY)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

sock.bind((MCAST_GRP, MCAST_PORT))

while 1:
    print("wait to receive data")
    d = sock.recvfrom(1024)
    data = d[0]
    addr = d[1]
    print("received " + data.decode())
    if not data:
        break
    reply = "ACK : " + data.decode()
    print ('Message[' + addr[0] + ':' + str(addr[1]) + '] - ' + data.decode().strip())

    reply = input("Send ack answer: ")

    print("going to send")
    # string2send =
    sock.sendto((data.decode() + " is a prime number? " + str(isprime(int(data.decode())))).encode(), addr)

sock.close()
