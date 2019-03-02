import socket

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10000
SERVICEID = 1

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)


print("Socket is ready")

# sock.sendto("Hello World", (MCAST_GRP, MCAST_PORT))
requestID = 0

while 1:
    try:
        int2check = input("int2check: ")
    except KeyboardInterrupt:
        print("Ending communication...")
        break

    if not int2check:
        print("Ending communication...")
        break

    # if isinstance(int(int2check), int):
    try:
        message2send = (SERVICEID, requestID, int(int2check))#, int(int2check)) #"ADD_SERVER")
    except ValueError as verror:
        message2send = (SERVICEID, requestID, int2check)


    print("Going to send: ", )
    sock.sendto(str(message2send).encode(), (MCAST_GRP, MCAST_PORT))
    print("Sent ",message2send)

    print("Going to wait")
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        print("Ending temp client/slave-server")
        break

    data = d[0]
    addr = d[1]

    print("Message[" + addr[0] + ":" + str(addr[1]) + "] : " + data.decode().strip())
    requestID = requestID + 1

sock.close()
