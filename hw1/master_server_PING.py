# Distributed Systems - hw1 :
# Asychronous request-reply with at most once and dynamic management of the servers
#                                                        (load balancing)
# Axelou Olympia 2161
# Tsitsopoulou Irene 2203
#
# master_server.py: The central part of the system
# Receives the requets from the clients and forwards them to one of the available servers
# Then, it receives the reply from the corresponding server and forwards it to the client
#

import sys
import time
import socket
import struct
import random
import threading
from threading import Thread
from  threading import Lock
from ast import literal_eval as make_tuple

# Some color defines for print
RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
ENDC   = '\033[0m'

# The pinned Multicast address and port
MCAST_GRP  = '224.0.0.1'
MCAST_PORT = 10300

# the initial weight of the requests
INITIAL_WEIGHT = 1

LOWER_THRESHOLD = 2
UPPER_THRESHOLD = 5

PING_PERIOD       = 0.5   # To periodically check the existence of the slave servers
STATISTICS_PERIOD = 0.1   # To periodically print the load and the #servers

# Thread that prints periodically (interval: STATISTICS_PERIOD sec) the total load and the number of servers
class StatisticsThreadClass(Thread):
    def run(self):
        while 1:
            lock.acquire()
            print("-> ", time.time(), "\tload: ", total_load, "\t#servers: ", len({k:v for k,v in serversdict.items() if v[2] == True}), file=sys.stderr)
            lock.release()
            time.sleep(STATISTICS_PERIOD)


################################################################################
# slave-server checker thread:
# Every PING_PERIOD seconds, it decrements the ping counter of each server
# in the serversdict and if it's less than zero, the corresponding server
# is removed from the dictionary, as it's considered "dead"
class PingReceiver(Thread):
    def run(self):
        global total_load
        while 1:
            time.sleep(PING_PERIOD)
            lock.acquire()
            # decrements the ping_number of every slave server in the system
            for server in serversdict:
                (srvcID, currentPingNumber, activeFlag, load) = serversdict[server]
                serversdict[server] = (srvcID, currentPingNumber - 1, activeFlag, load)
            # deletes every server with ping_number lower than zero
            # and checks if there is atleast one remaining that is active (v[2] == True)
            for server in list(serversdict.keys()):
                (_, currentPingNumber, _, load) = serversdict[server]
                if currentPingNumber < 0:
                    print(RED, "Going to remove server ", server, ENDC)
                    del serversdict[server]
                    if len({k:v for k,v in serversdict.items() if v[2] == True}) == 0:
                        server = random.choice(list(serversdict))
                        (srvcID, currentPingNumber, activeFlag, load) = serversdict[server]
                        serversdict[server] = (srvcID, currentPingNumber, True, load)
            # when load=0 leave only one server active and set everyone's load to zero
            if total_load == 0:
                while len({k:v for k,v in serversdict.items() if v[2] == True}) > 1:
                    server = random.choice(list({k:v for k,v in serversdict.items() if v[2] == True}))
                    (srvcID, currentPingNumber, _, load) = serversdict[server]
                    serversdict[server] = (srvcID, currentPingNumber, False, load)
                    print("No traffic, making only one server active")
                for server in serversdict:
                    (srvcID, currentPingNumber, activeFlag, _) = serversdict[server]
                    serversdict[server] = (srvcID, currentPingNumber, activeFlag, 0)
            # Check if there is at least one remaining server that is active (v[2] == True)
            if len({k:v for k,v in serversdict.items() if v[2] == True}) == 0 and len(list(serversdict)) > 0:
                server = random.choice(list({k:v for k,v in serversdict.items() if v[2] == False}))
                (srvcID, currentPingNumber, _, load) = serversdict[server]
                serversdict[server] = (srvcID, currentPingNumber, True, load)
                print("All remaining servers are inactive. Going to activate someone else")
            lock.release()

############################# Initializations ##################################

# Socket creation
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
sock.bind((MCAST_GRP, MCAST_PORT))

# init servers' and requests' dictionary + lock for servers
serversdict = {}
requestdict = {}
lock = Lock()

# init total load of the requests
total_load = 0

# Init ping - slave checker thread
pingthread = PingReceiver()
pingthread.daemon = True
pingthread.start()

# Init delay and #servers statistics thread
statisticsThread = StatisticsThreadClass()
statisticsThread.daemon = True
statisticsThread.start()

################################ MAIN CODE #####################################

while 1:
    try:
        d = sock.recvfrom(1024)
    except KeyboardInterrupt:
        print("Ending master server...")
        break
    data = d[0]
    addr = d[1]
    if not data:
        break
    # Unpack message received from the sender.
    # Should be a tuple with (srvcid, reqid/<ignoreValue>, int2check/message-from-server))
    try:
        (checkServiceID, reqID, message) = make_tuple(data.decode())
    except ValueError as verror:
        print("Received message with", verror)
        print("Going to ignore it...")
        continue

    lock.acquire()


    # received a ping message from a slave server
    if isinstance(message, tuple) and message[1] == 'ping':
        if addr in serversdict:    # server in dictionary, just going to increment ping number
            (srvcID, currentPingNumber, activeFlag, load) = serversdict[addr]
            serversdict[addr] = (srvcID, currentPingNumber + 1, activeFlag, load)
        else:                      # server not in dictionary, going to add it
            print(BLUE, "Accidentally removed ", addr, ". Going to add it again", ENDC)
            if addr not in serversdict:
                if len(serversdict) == 0:
                    serversdict[addr] = (message[0], 3, True, 0)
                else:
                    # checks if the serviceID matches with the one of the other servers connected to the master
                    randomServerInDictionary = random.choice(list({k:v for k,v in serversdict.items()}))
                    (serviceID, _, _, _) = serversdict[randomServerInDictionary]
                    if message[0] == serviceID:
                        serversdict[addr] = (message[0], 3, False, 0)
                    else:
                        print("Another service is running on the servers. You can't register.")
                        sock.sendto(str(((0, 0), 0, 1)).encode(), addr)

    # Received answer from a slave server
    elif (addr in serversdict ) and not isinstance(message, tuple):
        key = (checkServiceID[0], checkServiceID[1], reqID)
        if key in requestdict:
            # send reply to client
            (_, _, reqID2send) = key
            sock.sendto(str((reqID2send, message)).encode(), (key[0],key[1]))
            # remove request from requsts' dictionary and decrement total load and the server's load
            (_, load_freed, _) = requestdict[key]
            total_load -= load_freed
            print("\t Load less than before: ", total_load + load_freed, ", -> ", total_load)
            (srvcID, currentPingNumber, activeFlag, load) = serversdict[addr]
            serversdict[addr] = (srvcID, currentPingNumber, activeFlag, load - load_freed)
            # Deactivates the server with the min load if total_load/#servers is less than lower threshold
            if len({k:v for k,v in serversdict.items() if v[2] == True}) > 1 and (total_load / len({k:v for k,v in serversdict.items() if v[2] == True})) < LOWER_THRESHOLD :
                print("\n\n\n\n ", YELLOW, "Reached lower threshold. Going to deactivate one server. Total #servers: ", len({k:v for k,v in serversdict.items() if v[2] == True}), ENDC)
                activeServers = {k:v for k,v in serversdict.items() if v[2] == True}
                print(" activeServers: ", activeServers)
                #  search for the server with the minimum load
                serverToDeactivate = random.choice(list(activeServers))
                (_, _, _, minimum) = activeServers[serverToDeactivate]
                for server in activeServers:
                    (_, _, _, load) = activeServers[server]
                    if load < minimum:
                        minimum = load
                        serverToDeactivate = server
                print(GREEN, "server to deactivate: ", serverToDeactivate, ENDC)
                (srvcID, currentPingNumber, _, load) = serversdict[serverToDeactivate]
                serversdict[serverToDeactivate] = (srvcID, currentPingNumber, False, load)
            requestdict.pop(key)
        else:
            print("RequestID is not in the requests' dictionary. Going to discard this result")

    # Received a "register" message
    elif isinstance(message, tuple) and message[1] == "ADD_SERVER":
        print(BLUE, "A new server is available @ ", addr[0], "&", addr[1], ENDC)
        if addr not in serversdict:
            if len(serversdict) == 0:
                serversdict[addr] = (message[0], 3, True, 0)
            else:
                # checks if the serviceID matches with the one of the other servers connected to the master
                randomServerInDictionary = random.choice(list({k:v for k,v in serversdict.items()}))
                (serviceID, _, _, _) = serversdict[randomServerInDictionary]
                if message[0] == serviceID:
                    serversdict[addr] = (message[0], 3, False, 0)
                else:
                    print("Another service is running on the servers. You can't register.")
                    sock.sendto(str(((0, 0), 0, 1)).encode(), addr)

    # Received an "unregister" message
    elif isinstance(message, tuple) and isinstance(message, tuple) and message[1] == "RMV_SERVER":
        print("server unregistering @ ", addr[0], "&", addr[1])
        if addr in serversdict:
            del serversdict[addr]

    # Received a request from a client
    else:
        if not serversdict:
            print("There is no slave-server available in general")
            sock.sendto(str(( reqID, "NO-SERVER")).encode(), addr)
        else:
            try:
                # if (total_load / len(serversdict)) > UPPER_THRESHOLD then activates a random server
                if len({k:v for k,v in serversdict.items() if v[2] == True}) < len(serversdict) and ((total_load + 1) / len({k:v for k,v in serversdict.items() if v[2] == True})) > UPPER_THRESHOLD:
                    print("\n\n", YELLOW,"Reached upper threshold. Going to activate one more server. Total #servers: ", len({k:v for k,v in serversdict.items() if v[2] == True}), ENDC)
                    serverToActivate = random.choice(list({k:v for k,v in serversdict.items() if v[2] == False}))
                    print(BLUE, "server to activate: ", serversdict[serverToActivate], ENDC)
                    (srvcID, currentPingNumber, _, load) = serversdict[serverToActivate]
                    serversdict[serverToActivate] = (srvcID, currentPingNumber, True, load)
                # find all servers available for this serviceID
                serversAvailable4thisServiceID = {k:v for k,v in serversdict.items() if v[0] == checkServiceID and v[2] == True}
                if not serversAvailable4thisServiceID:
                    print("\n\nThere are no servers available for this serviceID: ", checkServiceID)
                    sock.sendto(str(( reqID, "NO-SERVER")).encode(), addr)
                    lock.release()
                    continue
                #  find server with the minimum load
                server2send2 = random.choice(list(serversAvailable4thisServiceID))
                (_, _, _, minimum) = serversAvailable4thisServiceID[server2send2]
                for server in serversAvailable4thisServiceID:
                    (_, _, _, load) = serversAvailable4thisServiceID[server]
                    if load < minimum:
                        minimum = load
                        server2send2 = server
                # Check if this is the first time the client sents this request
                # then add it to the requests' dict and assign it to the server from above
                # and increase total load
                if (addr[0], addr[1], reqID) not in requestdict:
                    sock.sendto(str((addr, reqID, message)).encode(), server2send2)
                    print(YELLOW, "New: ", (addr[0], addr[1], reqID),  ENDC)
                    requestdict[(addr[0], addr[1], reqID)] = (message, INITIAL_WEIGHT, server2send2)
                    total_load += INITIAL_WEIGHT
                    (srvcID, currentPingNumber, activeFlag, load) = serversdict[server2send2]
                    serversdict[server2send2] = (srvcID, currentPingNumber, activeFlag, load + 1)
                else: # if diplotupo, then it increases the request's weight
                    (_, weight, serverHandlingIt) = requestdict[(addr[0], addr[1], reqID)]
                    requestdict[(addr[0], addr[1], reqID)] = (message, weight + 1, serverHandlingIt)
                    total_load += 1
                    # if server handling it is ok then just increase its load, otherwise assign the
                    # the request to the server with the min load that has been found from above
                    if serverHandlingIt in serversAvailable4thisServiceID:
                        (srvcID, currentPingNumber, activeFlag, load) = serversdict[serverHandlingIt]
                        serversdict[serverHandlingIt] = (srvcID, currentPingNumber, activeFlag, load + 1)
                    else:
                        print("Server ", serverHandlingIt, "was handling this request but now he is dead. Going to send it to another one")
                        print("From search, next best choice: ", server2send2)
                        sock.sendto(str((addr, reqID, message)).encode(), server2send2)
                        requestdict[(addr[0], addr[1], reqID)] = (message, weight + 1, server2send2)
                        (srvcID, currentPingNumber, activeFlag, serverload) = serversdict[server2send2]
                        serversdict[server2send2] = (srvcID, currentPingNumber, activeFlag, serverload + weight + 1)
            except ZeroDivisionError:
                print("No active server. Trying again: ")
    lock.release()


sock.close()
print("Master sender quiting...")
