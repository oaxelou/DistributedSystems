import socket

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)


print("Socket is ready")

# sock.sendto("Hello World", (MCAST_GRP, MCAST_PORT))


while 1:
    int2check = input("int2check: ")
    print("Going to send")
    sock.sendto(int2check.encode(), (MCAST_GRP, MCAST_PORT))
    print("Sent " + int2check)
    if not int2check.encode():
        break

    print("Going to wait")
    d = sock.recvfrom(1024)
    data = d[0]
    addr = d[1]

    if not data:
        break

    print("Message[" + addr[0] + ":" + str(addr[1]) + "] : " + data.decode().strip())

sock.close()
