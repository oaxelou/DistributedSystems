import socket
import struct
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
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,socket.inet_aton(get_local_ip()))
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# mreq = socket.inet_aton(MCAST_GRP) + str(socket.INADDR_ANY)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
sock.bind((MCAST_GRP, MCAST_PORT))

# init servers' list and requests' dictionary
serverslist = []
requestdict = {}

while 1:
    print("wait to receive data")
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        print("Ending master server...")
        break

    data = d[0]
    addr = d[1]
    print("received " + data.decode())
    if not data:
        break

    # Unpack message received from the sender.
    # Should be a tuple with (srvcid, reqid/<ignoreValue>, int2check/"ADD_SERVER"))
    try:
        (checkServiceID, reqID, message) = make_tuple(data.decode())
    except ValueError as verror:
        print("Received message with", verror)
        print("Going to ignore it...")
        continue


    if checkServiceID != SERVICEID:
        print("This server can not process requests with service id '", checkServiceID, "'")
    else:
        if message == "ADD_SERVER": #(SERVICEID, "ADD_SERVER"):
            print("A new server is available @ ", addr[0], "&", addr[1])
            # adding server in serverslist IF IT IS NOT IN THERE ALREADY
            if addr not in serverslist:
                serverslist.append(addr)
                print("Going to print updated serverslist:")
            else:
                print("Server already registered! Going to print list anyway")
            print(serverslist)
            sock.sendto("ack - Hello new server".encode(), addr)

        elif addr in serverslist:
            print("A slave-server found a result and it's time to sendreply to client!")
            sock.sendto("ack - Good job, you slave".encode(), addr)
            # send reply to client
            # remove request from dict

        elif isinstance(message, int):
            print ('Message[',addr[0],':', addr[1], '] - ', data.decode())
            #adding request in requestdict (pros to paron to exw balei na apothikeuei to message)
            # ti na to valoume na apothikeuei den kserw.
            # PANTWS PREPEI NA VRISKEI KAPOION SERVER APO TH LISTA TWN SERVERS
            requestdict[(addr[0], addr[1], reqID)] = message
            print("Added new request in dict.")
            print(requestdict)
            # h apo katw grammh tha mpei ston slave-server
            #answer2send = "ack - " + str(message) + " is" + (" not " if not isprime(message) else " ") + "prime"
            answer2send = "ack - received " + str(message)
            sock.sendto(answer2send.encode(), addr)

        else:
            print("Service ID is ok but the message is unrecognizable")
            print("Going to ignore this...")
            sock.sendto("ack - Who are you mate?".encode(), addr)



sock.close()
