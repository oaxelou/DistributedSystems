import socket
import struct
from ast import literal_eval as make_tuple
import time
import random
import threading
from threading import Thread
from  threading import Lock

WARNING = '\033[93m'
ENDC = '\033[0m'

MCAST_GRP = '224.0.0.1'
MCAST_PORT = 10300
# will not be defined if we have multiple services
# SERVICEID = 1
INITIAL_WEIGHT = 1

LOWER_THRESHOLD = 10
UPPER_THRESHOLD = 20

PERIOD = 5
################################################################################
# slave-server checker thread code
class PingReceiver(Thread):
    def run(self):
        global total_load
        while 1:
            time.sleep(PERIOD)
            lock.acquire()
            for server in serversdict:
                # print("Decrementing value of ", server)
                (srvcID, currentPingNumber, activeFlag, load) = serversdict[server]
                serversdict[server] = (srvcID, currentPingNumber - 1, activeFlag, load)

            for server in list(serversdict.keys()):
                (_, currentPingNumber, _, load) = serversdict[server]
                if currentPingNumber < 0:
                    print("!!!!!!!!!!!!!!!Going to remove server ", server)
                    # total_load -= load
                    del serversdict[server]
                    if len({k:v for k,v in serversdict.items() if v[2] == True}) == 0:
                        server = random.choice(list(serversdict))
                        (srvcID, currentPingNumber, activeFlag, load) = serversdict[server]
                        serversdict[server] = (srvcID, currentPingNumber, True, load)

            if total_load == 0:
                while len({k:v for k,v in serversdict.items() if v[2] == True}) > 1:
                    server = random.choice(list({k:v for k,v in serversdict.items() if v[2] == True}))
                    (srvcID, currentPingNumber, _, load) = serversdict[server]
                    serversdict[server] = (srvcID, currentPingNumber, False, load)
                    print("no traffic, making only one server active")
            # dict((key, value) for key, value in serversdict.items() if value>0)
            # for server in :
            #     serversdict[server] -= 1
            #     if serversdict[server] == 0:
            #         print("No ping from ", server, ". I am going to remove it")
            #         serversdict.pop(server)
            lock.release()


################################################################################
# Initializations

# Socket creation
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,socket.inet_aton(get_local_ip()))
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
# mreq = socket.inet_aton(MCAST_GRP) + str(socket.INADDR_ANY)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
sock.bind((MCAST_GRP, MCAST_PORT))


# init servers' and requests' dictionary + lock for servers
serversdict = {}
requestdict = {}
lock = Lock()

# Init ping thread
pingthread = PingReceiver()
pingthread.daemon = True
pingthread.start()

# init total load of the requests
total_load = 0


################################################################################

while 1:
    print("wait to receive data")
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        print("Ending master server...")
        break

    data = d[0]
    addr = d[1]
    # print("received " + data.decode())
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

    lock.acquire()
    print(" ")
    print(" ")
    print("requestdict: ")
    print(requestdict)
    print("serversdict")
    print(serversdict)
    print("total load = ", total_load)
    # Received an assurement
    if isinstance(message, tuple) and message[1] == 'ping':
        if addr in serversdict:
            (srvcID, currentPingNumber, activeFlag, load) = serversdict[addr]
            serversdict[addr] = (srvcID, currentPingNumber + 1, activeFlag, load)
        else:
            # print("Accidentally removed ", addr, ". Going to add it again")
            if addr not in serversdict:
                if len(serversdict) == 0:
                    serversdict[addr] = (message[0], 2, True, 0)
                else:
                    serversdict[addr] = (message[0], 2, False, 0)

    # Received answer from a slave server
    elif (addr in serversdict ) and not isinstance(message, tuple):
        key = (checkServiceID[0], checkServiceID[1], reqID)
        if key in requestdict:
            # send reply to client
            (_, _, reqID2send) = key
            sock.sendto(str((reqID2send, message)).encode(), (key[0],key[1]))
            # remove request from dict
            (_, load_freed, _) = requestdict[key]
            total_load -= load_freed
            (srvcID, currentPingNumber, activeFlag, load) = serversdict[addr]
            serversdict[addr] = (srvcID, currentPingNumber, activeFlag, load - load_freed)
            print("\t Load less than before: ", total_load)

            if (total_load / len({k:v for k,v in serversdict.items() if v[2] == True})) < LOWER_THRESHOLD and len({k:v for k,v in serversdict.items() if v[2] == True}) > 1 :
                print("\n\n\n\n\n\n\n\n Reached lower threshold. Going to deactivate one server. Total #servers: ", len({k:v for k,v in serversdict.items() if v[2] == True}))
                serverToDeactivate = addr  # autos pou molis afhse thn aithsh
                print("server to deactivate: ", serversdict[serverToDeactivate])
                (srvcID, currentPingNumber, _, load) = serversdict[serverToDeactivate]
                serversdict[serverToDeactivate] = (srvcID, currentPingNumber, False, load)
            requestdict.pop(key)
        # else:
            # print("Going to discard this result")

    # Received a "register" message
    elif isinstance(message, tuple) and message[1] == "ADD_SERVER":
        print("A new server is available @ ", addr[0], "&", addr[1])
        # clearing list before adding the server. There is only one server at a time
        serversdict.clear()
        # adding server in serversdict IF IT IS NOT IN THERE ALREADY
        if addr not in serversdict:
            if len(serversdict) == 0:
                serversdict[addr] = (message[0], 2, True, 0)
            else:
                serversdict[addr] = (message[0], 2, False, 0)


    # Received an "unregister" message
    elif isinstance(message, tuple) and isinstance(message, tuple) and message[1] == "RMV_SERVER":
        print("server unregistering @ ", addr[0], "&", addr[1])
        # clearing list before adding the server. There is only one server at a time
        if addr in serversdict:
            del serversdict[addr]

    # Received a request from a client
    else:
        # print ('Message[',addr[0],':', addr[1], '] - ', data.decode())
        #adding request in requestdict (pros to paron to exw balei na apothikeuei to message)
        # ti na to valoume na apothikeuei den kserw.
        # PANTWS PREPEI NA VRISKEI KAPOION SERVER APO TH LISTA TWN SERVERS
        if not serversdict:
            print("There is no slave-server available")
            sock.sendto(str(( reqID, "NO-SERVER")).encode(), addr)
        else:
            # koitaei to total_load kai an (total_load / len(serversdict)) > UPPER_THRESHOLD tote thetei kapoion sthn tuxh ws True (active)
            if ((total_load + 1) / len({k:v for k,v in serversdict.items() if v[2] == True})) > UPPER_THRESHOLD and len({k:v for k,v in serversdict.items() if v[2] == True}) < len(serversdict):
                print("\n\n\n\n\n\n\n\n Reached upper threshold. Going to activate one more server. Total #servers: ", len({k:v for k,v in serversdict.items() if v[2] == True}))
                serverToActivate = random.choice(list({k:v for k,v in serversdict.items() if v[2] == False}))
                print("server to activate: ", serversdict[serverToActivate])
                (srvcID, currentPingNumber, _, load) = serversdict[serverToActivate]
                serversdict[serverToActivate] = (srvcID, currentPingNumber, True, load)
            # vrikei kapoio server (sto part 1 pairnoume to 1o kai monadiko)
            # server2send2 = random.choice(list(serversdict.keys()))
            serversAvailable4thisServiceID = {k:v for k,v in serversdict.items() if v[0] == checkServiceID and v[2] == True}
            print(" serversAvailable4thisServiceID: ", serversAvailable4thisServiceID)
            if not serversAvailable4thisServiceID:
                print("\n\nThere are not servers available for this serviceID")
                sock.sendto(str(( reqID, "NO-SERVER")).encode(), addr)
                lock.release()
                continue
            #  search for the server with the minimum load
            server2send2 = random.choice(list(serversAvailable4thisServiceID))
            (_, _, _, minimum) = serversAvailable4thisServiceID[server2send2]
            for server in serversAvailable4thisServiceID:
                (_, _, _, load) = serversAvailable4thisServiceID[server]
                if load < minimum:
                    minimum = load
                    server2send2 = server

            # server2send2 = min(serversdict, key=serversdict.get)
            # stelnoume ston server pou vrikame olo to d + requestID
            # print("Found a server to send to: ", server2send2)

            if (addr[0], addr[1], reqID) not in requestdict:
                sock.sendto(str((addr, reqID, message)).encode(), server2send2)
                print(WARNING, "New:", ENDC)
                # serversdict[server2send2]
                requestdict[(addr[0], addr[1], reqID)] = (message, INITIAL_WEIGHT, server2send2)
                total_load += INITIAL_WEIGHT
                # print("server2send2[0] ", server2send2)
                (srvcID, currentPingNumber, activeFlag, load) = serversdict[server2send2]
                serversdict[server2send2] = (srvcID, currentPingNumber, activeFlag, load + 1)

                # print("\tFirst time getting this request. Current load: ", total_load)
            else:
                (_, weight, serverHandlingIt) = requestdict[(addr[0], addr[1], reqID)]
                print(WARNING, "Weight:", weight, ENDC)
                requestdict[(addr[0], addr[1], reqID)] = (message, weight + 1, serverHandlingIt)
                total_load += 1
                if serverHandlingIt in serversdict:
                    (srvcID, currentPingNumber, activeFlag, load) = serversdict[serverHandlingIt]
                    serversdict[serverHandlingIt] = (srvcID, currentPingNumber, activeFlag, load + 1)
                    # print("\tNot! the first time getting this request. Current load: ", total_load)
                else:
                    print("Server ", serverHandlingIt, "was handling this request but now he is dead. Going to send it to another one")
                    print("From search, next best choice: ", server2send2)
                    sock.sendto(str((addr, reqID, message)).encode(), server2send2)
                    requestdict[(addr[0], addr[1], reqID)] = (message, weight + 1, server2send2)
                    # total_load += weight
                    (srvcID, currentPingNumber, activeFlag, serverload) = serversdict[server2send2]
                    serversdict[server2send2] = (srvcID, currentPingNumber, activeFlag, serverload + weight + 1)


                # na auksanetai kai to load sto serversdict


    # else:
    #     print("Service ID is ok but the message is unrecognizable")
    #     print("Going to ignore this...")
    #     sock.sendto("ack - Who are you mate?".encode(), addr)
    lock.release()


sock.close()
print("Master sender quiting...")
