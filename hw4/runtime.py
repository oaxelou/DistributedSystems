import time
import threading
from threading import Thread
from threading import Lock
import socket
import sys
import struct
from ast import literal_eval as make_tuple
import struct
# from user_interface import user_interface

arithmetic = ["ADD", "SUB", "MUL", "DIV", "MOD"]
branch = ["BGT", "BGE", "BLT", "BLE", "BEQ"]
csp = ["SND", "RCV"]

program_dictionary = {}
program_dictionary_lock = Lock()

######## COLORS #######
RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
ENDC   = '\033[0m'

######## STATE DEFINES #######
RUNNING = 0
READY = 1
BLOCKED =  2
ENDED = 3

#### BLOCKED FIELD DEFINES ###
NOT_BLOCKED = 0
SLEEPING = 1
RECEIVING = 2
SENDING = 3
DELIVERING = 4

BLOCKED_TYPE = 0
SLEEPING_TIME_EXPECTED_MES = 1
RCV_BUFFER = 2

######## FIELD DEFINES #######
NAME_FIELD = 0
ARGS_FIELD = 1
THREAD_FIELD = 2
GROUP_FIELD = 3
IP_FIELD = 4
STATE_FIELD = 5
BLOCKED_INFO_FIELD = 6
PC_FIELD = 7
INSTR_FIELD = 8
LABEL_FIELD = 9
VAR_FIELD = 10

######## FIELD DEFINES #######
INSTR_TIME_ON_CPU = 5

### RUN_COMMAND RETURN VALUES ###
NORMAL_PC_INCR = -1
UNDEFINED_VAR = -2


################# CLASSES #################
def setSleep(key, interval):
    global program_dictionary
    global program_dictionary_lock
    print("Going to sleep for ", interval, "secs")
    (name, args, threadID, groupID, IP, _, blocked_info, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, threadID, groupID, IP, BLOCKED, (SLEEPING, (time.time(), interval), blocked_info[RCV_BUFFER]), program_counter, instr_dict, labels_dict, var_dict)

def setState(key, newState):
    global program_dictionary
    global program_dictionary_lock
    (name, args, threadID, groupID, IP, oldState, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    print("Going to set ", key, " from ", oldState, " to ", newState)
    program_dictionary[key] = (name, args, threadID, groupID, IP, newState, blockedInfo, program_counter, instr_dict, labels_dict, var_dict)

def setBlockedState(key, newState):
    global program_dictionary
    global program_dictionary_lock
    (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    (blocked_State, expected_message, rcv_buffer) = blockedInfo
    blockedInfo = (newState, expected_message, rcv_buffer)
    print("Going to set ", key, " from ", blocked_State, " to ", newState)
    if state != BLOCKED:
        print("Something went terribly wrong with setting blocked state")
        exit(1)
    program_dictionary[key] = (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict)

def setReceive(key, sender, varname): # block because of waiting for a message
    global program_dictionary
    global program_dictionary_lock
    print("Going to wait for a message from ", sender)
    (name, args, threadID, groupID, IP, _, blocked_info, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, threadID, groupID, IP, BLOCKED, (RECEIVING, (sender, varname), blocked_info[RCV_BUFFER]), program_counter, instr_dict, labels_dict, var_dict)

# done
def setDeliver(key, receiver, message): # set message to blocked
    global program_dictionary
    global program_dictionary_lock
    print("Going to deliver message to ", receiver)
    (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    (blockType, _, msg_buffer) = blockedInfo
    blockedInfo = (SENDING, (receiver, message), msg_buffer)
    program_dictionary[key] = (name, args, threadID, groupID, IP, BLOCKED, blockedInfo, program_counter, instr_dict, labels_dict, var_dict)

def increment_pc(key, new_pc):
    global program_dictionary
    global program_dictionary_lock
    (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    # print("going to change pc from, ", program_counter, "to ", new_pc)
    program_dictionary[key] = (name, args, threadID, groupID, IP, state, blockedInfo, new_pc, instr_dict, labels_dict, var_dict)

def check_varval_int(varval, key):
    if varval[0] == '$':
        if varval not in program_dictionary[key][VAR_FIELD]:
            return -1
        else:
            print("VAR")
            return 'var'
    else:
        return 'val'

def run_command(key, command):
    global program_dictionary
    global program_dictionary_lock

    if command[0] == 'SET':
        var = command[1]
        varval = command[2]
        # could be either string or variable or integer
        if varval[0] == '\"':
            print("varval is a string")
            program_dictionary[key][VAR_FIELD][var] = varval

        # else if varval is a variable
        elif varval[0] == '$':
            if varval not in program_dictionary[key][VAR_FIELD]:
                print(varval, "not defined")
                return UNDEFINED_VAR

            else:
                program_dictionary[key][VAR_FIELD][var] = program_dictionary[key][VAR_FIELD][varval]
        else:
            print("varval is an int:", int(varval))
            # mporei na ginei kai xwris to int
            # kai na ginetai apo tis entoles pou kanoun praxeis
            program_dictionary[key][VAR_FIELD][var] = int(varval)

    elif command[0] in arithmetic:
        var = command[1]
        # varval1 = command[2]
        # varval2 = command[3]

        if check_varval_int(command[2], key) == 'var':
            varval1 = program_dictionary[key][VAR_FIELD][command[2]]
        elif check_varval_int(command[2], key) == 'val':
            varval1 = int(command[2])
        else:
            print(command[2], "not defined")
            return UNDEFINED_VAR

        if check_varval_int(command[3], key) == 'var':
            varval2 = program_dictionary[key][VAR_FIELD][command[3]]
        elif check_varval_int(command[3], key) == 'val':
            varval2 = int(command[3])
        else:
            print(command[3], "not defined")
            return UNDEFINED_VAR

        if command[0] == 'ADD':
            program_dictionary[key][VAR_FIELD][var] = varval1 + varval2
        elif command[0] == 'SUB':
            program_dictionary[key][VAR_FIELD][var] = varval1 - varval2
        elif command[0] == 'MUL':
            program_dictionary[key][VAR_FIELD][var] = varval1 * varval2
        elif command[0] == 'DIV':
            program_dictionary[key][VAR_FIELD][var] = varval1 / varval2
        elif command[0] == 'MOD':
            program_dictionary[key][VAR_FIELD][var] = varval1 % varval2

    elif command[0] in branch:
        # varval1 = command[1]
        # varval2 = command[2]
        # label = command[3]

        if check_varval_int(command[1], key) == 'var':
            varval1 = program_dictionary[key][VAR_FIELD][command[1]]
        elif check_varval_int(command[1], key) == 'val':
            varval1 = int(command[1])
        else:
            print(command[1], "not defined")
            return UNDEFINED_VAR

        if check_varval_int(command[2], key) == 'var':
            varval2 = program_dictionary[key][VAR_FIELD][command[2]]
        elif check_varval_int(command[2], key) == 'val':
            varval2 = int(command[2])
        else:
            print(command[2], "not defined")
            return UNDEFINED_VAR


        # at this point we know that the label we want to jump to exists
        # find label in labels_dict and change program counter
        # labels are in program_dictionary[key][LABEL_FIELD]

        try:
            new_pc = program_dictionary[key][LABEL_FIELD][command[3]]
        except KeyError:
            print("No such label")
            return UNDEFINED_VAR
        if command[0] == 'BEQ':
            if varval1 == varval2:
                return new_pc
        elif command[0] == 'BGE':
            if varval1 >= varval2:
                return new_pc
        elif command[0] == 'BGT':
            if varval1 > varval2:
                return new_pc
        elif command[0] == 'BLE':
            if varval1 <= varval2:
                return new_pc
        elif command[0] == 'BLT':
            if varval1 < varval2:
                return new_pc

    elif command[0] == 'BRA':
        try:
            new_pc = program_dictionary[key][LABEL_FIELD][command[1]]
        except KeyError:
            print("No such label")
            return UNDEFINED_VAR
        return new_pc

    elif command[0] == 'SLP':
        # varval1 = command[1]

        if check_varval_int(command[1], key) == 'var':
            varval1 = program_dictionary[key][VAR_FIELD][command[1]]
        elif check_varval_int(command[1], key) == 'val':
            varval1 = int(command[1])
        else:
            print(command[1], "not defined")
            return UNDEFINED_VAR

        setSleep(key, varval1)

    elif command[0] == 'PRN':
        string2print = ""
        for arg in command[1:]:
            # print(BLUE, arg, ENDC)
            if arg[0] == '$':
                if arg not in program_dictionary[key][VAR_FIELD]:
                    print(arg, "not defined")
                    return UNDEFINED_VAR
                else:
                    string2print += str(program_dictionary[key][VAR_FIELD][arg]) + " "
            else:
                if arg[0] == '\"':
                    string2print += arg[1:-1] + " "
                else:
                    string2print += str(arg) + " "
        print(RED, "Group ", program_dictionary[key][GROUP_FIELD], ", Thread ", program_dictionary[key][THREAD_FIELD][1], ":", string2print, ENDC)

    elif command[0] == 'RET':
        setState(key, ENDED)

    elif command[0] == 'SND':
        if check_varval_int(command[1], key) == 'var':
            thread2send2 = program_dictionary[key][VAR_FIELD][command[1]]
        elif check_varval_int(command[1], key) == 'val':
            thread2send2 = int(command[1])
        else:
            print(command[1], "not defined")
            return UNDEFINED_VAR
        setDeliver(key, thread2send2, command[2])  # mesa sthn setDeliver allazei to state se BLOCKED

    elif command[0] == 'RCV':
        if check_varval_int(command[1], key) == 'var':
            senderthread = program_dictionary[key][VAR_FIELD][command[1]]
        elif check_varval_int(command[1], key) == 'val':
            senderthread = int(command[1])
        else:
            print(command[1], "not defined")
            return UNDEFINED_VAR
        setReceive(key, senderthread, command[2])  # mesa sthn setReceive allazei to state se BLOCKED
    # unless there is a jump, return -1 aka NORMAL_PC_INCR
    return NORMAL_PC_INCR

def kill(groupID):
    global program_dictionary
    global program_dictionary_lock
    programs_killed = 0
    for program in program_dictionary:
        program_groupID = program_dictionary[program][GROUP_FIELD]
        print(GREEN, "Going to check if ", program_groupID, "==", groupID, ENDC)
        if str(program_groupID) == groupID:
            print(GREEN, "Going to kill ", program, ENDC)
            setState(program, ENDED)
            programs_killed += 1
    print("Programs Killed: ", programs_killed)
def kill_whole_group(key):
    global program_dictionary
    global program_dictionary_lock
    print("Going to kill ", key, " and its group")
    (_, _, _, my_groupID, _, _, _, _, _, _, _) = program_dictionary[key]
    kill(my_groupID)
    setState(key, ENDED)

def dealWithReady(key):
    global program_dictionary
    global program_dictionary_lock

    setState(key, RUNNING)
    print(YELLOW, key, " is running", ENDC)
    for i in range(INSTR_TIME_ON_CPU):
        print(YELLOW, "running command", ENDC)
        pc = program_dictionary[key][PC_FIELD]
        command = program_dictionary[key][INSTR_FIELD][pc]

        new_pc = run_command(key, command) # returns -1 if there is no branch
        print("after run command: command =", command[0], "new_pc == ", new_pc)
        print(GREEN, program_dictionary[key][VAR_FIELD], ENDC)
        # setSleep(key, 5)       # debugging stuff
        # if i == 2:               # debugging stuff
        #     setReceive(key, 1)   # debugging stuff

        # increment program counter
        if new_pc == NORMAL_PC_INCR:
            increment_pc(key, pc+1)
        elif new_pc == UNDEFINED_VAR:
            # kill program and its group
            kill_whole_group(key)
        else:
            increment_pc(key, new_pc)

        if program_dictionary[key][STATE_FIELD] != RUNNING:
            print("Program blocked or ended")
            break
        # time.sleep(1.5)

    if program_dictionary[key][STATE_FIELD] == RUNNING:
        print("Program not over yet but going to leave CPU")
        setState(key, READY)

class InterpreterThread(Thread):
    def run(self):
        global program_dictionary
        global program_dictionary_lock

        while True:
            program_dictionary_lock.acquire()
            for key in program_dictionary:
                if program_dictionary[key][STATE_FIELD] == READY:
                    dealWithReady(key)
                else:
                    print(YELLOW, key, " is NOT running", ENDC)
            program_dictionary_lock.release()
            time.sleep(1.5)

###################################
def dealWithBlocked(key):
    global program_dictionary
    global program_dictionary_lock

    print("Program ", key, " is blocked.")
    if program_dictionary[key][BLOCKED_INFO_FIELD][0] == SLEEPING:
        print("Going to check if time has passed")
        timeElapsed = program_dictionary[key][BLOCKED_INFO_FIELD][1][0] + program_dictionary[key][BLOCKED_INFO_FIELD][1][1]
        if time.time() >= timeElapsed:
            print("Program ", key, "has waken up from sleep")
            setState(key, READY)
    else:
        # print("Going to check if message is here")
        (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
        if program_dictionary[key][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == SENDING:
            (receiver, message) = program_dictionary[key][BLOCKED_INFO_FIELD][SLEEPING_TIME_EXPECTED_MES]
            foundReceiver = False
            for program in program_dictionary:
                print(YELLOW, receiver, "Checking to send to ",program_dictionary[program][THREAD_FIELD], ENDC)
                if program_dictionary[program][THREAD_FIELD][1] == receiver:
                    print("Found the receiver")
                    foundReceiver = True
                    break
            if foundReceiver == False:
                print("In this runtime the receiver thread ", receiver, "does not exist")
                return
            program_dictionary[program][BLOCKED_INFO_FIELD][RCV_BUFFER].append((program_dictionary[key][THREAD_FIELD][1], message))
            setBlockedState(key, DELIVERING)
        elif program_dictionary[key][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == DELIVERING:
            (receiver, message) = program_dictionary[key][BLOCKED_INFO_FIELD][SLEEPING_TIME_EXPECTED_MES]
            foundReceiver = False
            for program in program_dictionary:
                print(YELLOW, receiver, "Checking to send to ",program_dictionary[program][THREAD_FIELD], ENDC)
                if program_dictionary[program][THREAD_FIELD][1] == receiver:
                    print("Found the receiver")
                    foundReceiver = True
                    break
            if foundReceiver == False:
                print("In this runtime the receiver thread ", receiver, "does not exist")
                return
            if (key, message) not in program_dictionary[program][BLOCKED_INFO_FIELD][RCV_BUFFER]:
                print("Message received.")
                setState(key, READY)
        elif program_dictionary[key][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == RECEIVING:
            # set program_dictionary here
            message2receive = program_dictionary[key][BLOCKED_INFO_FIELD][SLEEPING_TIME_EXPECTED_MES]
            print("Searching for ", message2receive)
            buffer = program_dictionary[key][BLOCKED_INFO_FIELD][RCV_BUFFER]
            try:
                print(message2receive[1])
                print("ok")
                print(message2receive[1][0])
                print("ok1")
                if message2receive[1][0] == '$':
                # if message2receive[1][0] == '$':
                    foundIt = False
                    for message in buffer:
                        print("ok2")
                        print(message)
                        if message2receive[0] == message[0]: # dhladh o sender na einai idios
                            print("ok3")
                            foundIt = True
                            break
                    if foundIt:
                        # store the value in message2receive[1] var
                        program_dictionary[key][VAR_FIELD][message2receive[1]] = message[1]
                        print("found it: Got the message I wanted: ", message2receive)
                        # print(RED, "will del buffer[message] =", buffer[message], ENDC)
                        # del buffer[message]
                        buffer.remove(message)
                        # set program_dictionary here
                        (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
                        program_dictionary[key] = (name, args, threadID, groupID, IP, READY, (0, 0, buffer), program_counter, instr_dict, labels_dict, var_dict)
                else:
                    if message2receive in buffer:
                        print("Got the message I wanted: ", message2receive)
                        # print(RED, "will del buffer[message] =", buffer[message2receive], ENDC)
                        # del buffer[message2receive]
                        buffer.remove(message2receive)
                        (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
                        program_dictionary[key] = (name, args, threadID, groupID, IP, READY, (0, 0, buffer), program_counter, instr_dict, labels_dict, var_dict)
            except TypeError:
                print("It's a value")
                print(buffer)
                if message2receive in buffer:
                    print("Got the message I wanted: ", message2receive)
                    # print(RED, "will del buffer[message] =", buffer[message2receive], ENDC)
                    # del buffer[message2receive]
                    buffer.remove(message2receive)
                    (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
                    program_dictionary[key] = (name, args, threadID, groupID, IP, READY, (0, 0, buffer), program_counter, instr_dict, labels_dict, var_dict)
        print(BLUE, program_dictionary[key][BLOCKED_INFO_FIELD][RCV_BUFFER], ENDC)
class BlockedManagerThread(Thread):
    def run(self):
        global program_dictionary
        global program_dictionary_lock

        while True:
            key2del = -1
            program_dictionary_lock.acquire()
            for key in program_dictionary:
                if program_dictionary[key][STATE_FIELD] == BLOCKED:
                    dealWithBlocked(key)
                elif program_dictionary[key][STATE_FIELD] == ENDED:
                    print(YELLOW, "Going to delete ", key, ENDC)
                    key2del = key
                    break

            if key2del >= 0:
                del program_dictionary[key2del]
            # else:
            #     print("Program ", key2del, " is not blocked. Going to try for another one")
            print(GREEN, program_dictionary, ENDC)
            program_dictionary_lock.release()
            time.sleep(1)
###########################################
# runtime_comm stuff

FRAG_SIZE = 75
UDP_SIZE = FRAG_SIZE + 64

# The pinned Multicast address and port
MCAST_GRP  = '224.0.0.1'
MCAST_PORT = 10300

################################################################################
def find_avl_port(sock, MY_IP):
    UDP_PORT = 1
    while True:
        try:
            sock.bind((MY_IP, UDP_PORT))
        except PermissionError:
            # print("Another app is using this port. I am going to try try with: ", UDP_PORT)
            UDP_PORT += 1
            continue
        except OSError:
            # print("Another app is using this port. I am going to try try with: ", UDP_PORT)
            UDP_PORT += 1
            continue

            break

        print("I am listening on port: ", UDP_PORT)
        return UDP_PORT

def get_IP():
    find_ip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        find_ip_sock.connect(('10.255.255.255', 1))
        IP = find_ip_sock.getsockname()[0]
    except:
        IP = '127.0.0.1'
    return IP

def fragNsend(sock, prog_dict_entry, address):
    program_dictionary_string = str(prog_dict_entry)
    # print(program_dictionary_string)
    # print("#################################################")
    program_dictionary_serialized = program_dictionary_string.encode()
    # print(program_dictionary_serialized)

    sock.sendto(str(("migrate", 0)).encode(), address)

    iter = 0
    while True:
        # bytes2send = string2send[iter:(iter+25)].encode()
        bytes2send = program_dictionary_serialized[iter:(iter+FRAG_SIZE-1)]
        print("going to send ", bytes2send)
        sock.sendto(bytes2send, address)
        iter += FRAG_SIZE-1
        if iter >= len(program_dictionary_serialized.decode()):
            break
            # if iter >= len(string2send):
            #     break
        # time.sleep(2)
    # send exit
    message = "EndOfTransmission"
    sock.sendto(str(message).encode(), address)

def global_ids_update(sock, next_group_id, next_thread_id, my_load):
    message = ("inform", (next_group_id, next_thread_id, my_load))
    sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))

class MulticastListener(Thread):
    def run(self):
        while True:
            global next_group_id
            global next_thread_id
            # init - receive IP from the other runtime
            d = mult_sock.recvfrom(UDP_SIZE)
            print(MY_IP, MY_PORT)
            print(d[1])
            if d[1] == (MY_IP, MY_PORT):
                continue
            data = make_tuple(d[0].decode())
            if data[0] == "hello":
                print("New runtime @ ", d[1])
                ids_lock.acquire()
                other_runtimes_dict[d[1]] = 0
                # my_load: vres to apo program_dictionary
                message = ("inform", (next_group_id, next_thread_id, my_load))
                sock.sendto(str(message).encode(), d[1])
                print(other_runtimes_dict)
                ids_lock.release()
            elif data[0] == "exit":
                ids_lock.acquire()
                if d[1] in other_runtimes_dict:
                    del other_runtimes_dict[d[1]]
                    print(other_runtimes_dict)
                ids_lock.release()
            elif data[0] == "inform":
                ids_lock.acquire()
                next_group_id, next_thread_id, load = data[1]
                if d[1] not in other_runtimes_dict:
                    other_runtimes_dict[d[1]] = load
                    print(other_runtimes_dict)
                ids_lock.release()

class ReceiverThread(Thread):
    def run(self):
        while True:
            # init - receive IP from the other runtime
            d = sock.recvfrom(UDP_SIZE)
            data = make_tuple(d[0].decode())
            print("I got: ", data)
            if data[0] == "migrate":
                program_dictionary_serialized = ""
                while True:
                    d = sock.recvfrom(UDP_SIZE)
                    # print("I received from ", d[1])
                    data = d[0].decode()
                    # print("data: ", data)
                    if data == "EndOfTransmission":
                        break
                    program_dictionary_serialized += data
                program_dictionary_entry = make_tuple(program_dictionary_serialized)
                # print("#################################################")
                print(program_dictionary_entry)
                print("command 5: ", program_dictionary_entry[5][5])

                # ADD IN program_dictionary
                # 1) na pairnei to pedio tou threadID kai na to xrhsimopoiei ws key
                # 2) an uparxei sleep na prosarmozei ton xrono (h mhpws to runtime pou to stelnei?)
                # 3) na allaksoume tin IP (h mhpws to runtime pou to stelnei?)
            elif data[0] == "inform":
                ids_lock.acquire()
                next_group_id, next_thread_id, load = data[1]
                if d[1] not in other_runtimes_dict:
                    other_runtimes_dict[d[1]] = load
                    print(other_runtimes_dict)
                ids_lock.release()
################################################################################

# init private socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
MY_IP = get_IP()
MY_PORT = find_avl_port(sock, MY_IP)
print(MY_IP)
print(MY_PORT)

other_runtimes_dict = {}

# # init program_dictionary
next_group_id = 0
next_thread_id = 0

message = ("hello", 0)
sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))

# Multicast Socket creation
mult_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
mult_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
mult_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

mult_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
mult_sock.bind((MCAST_GRP, MCAST_PORT))

ids_lock = Lock()

# multicast thread
multicastthread = MulticastListener()
multicastthread.daemon = True
multicastthread.start()

receiverthread = ReceiverThread()
receiverthread.daemon = True
receiverthread.start()

######################################################################################

# next_group_id  = 0
# next_thread_id = 0

blockedManager = BlockedManagerThread()
blockedManager.daemon = True
blockedManager.start()

interpreter = InterpreterThread()
interpreter.daemon = True
interpreter.start()

# Add a program in the program_dictionary
# program_dictionary_lock.acquire()
# name = "hello.c"
# argc, argv = 1, (name)
# args = (argc, argv)
# threadID = 0
# groupID = 0
# programID = 0
# state = READY
# blocked_info = 0 #(SLEEPING,(time.time(), 3)) # useful only when blocked
# program_counter = 0
# instr_dict = {0: ['BRA', '#lm'], 1: ['ADD', '$rr', '4', '3'], 2: ['SLP', '2'], 3: ['SUB', '$rv', '10', '1'], \
#                 4: ['ADD', '$rr', '4', '0'], 5: ['SUB', '$rv', '10', '0'], 6: ['ADD', '$rr', '0', '0'], 7: ['SUB', '$rv', '10', '5'], 8: ['RET']}
#
# # instr_dict = {0: ['PRN', '56', '"STRANG"'], 1: ['RET']}
# labels_dict = {'#lm': 2}
# var_dict = {}
#
# program_dictionary[0] = (name, args, threadID, groupID, programID, state, blocked_info, program_counter, instr_dict, labels_dict, var_dict)
# program_dictionary_lock.release()


# time.sleep(3)

# program_dictionary_lock.acquire()
# setDeliver(1, 0, "hi")
# program_dictionary[0] = (name, args, group, ENDED, 0, program_counter, instr_dict, labels_dict, var_dict)
# program_dictionary_lock.release()





# time.sleep(20)
# exit()
