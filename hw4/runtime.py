import time
import threading
from threading import Thread
from threading import Lock
import socket
import sys
import struct
from ast import literal_eval as make_tuple
import struct
from parser import *
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

other_runtimes_dict = {}

# # init program_dictionary
next_group_id = 0
next_thread_id = 0

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
        if program_dictionary[key][IP_FIELD][0] != program_dictionary[key][IP_FIELD][1]:
            message = ("print", key, string2print)
            sock.sendto(str(message).encode(), program_dictionary[key][IP_FIELD][0])
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
        # print(GREEN, "Going to check if ", program_groupID, "==", groupID, ENDC)
        if str(program_groupID) == groupID:
            if program_dictionary[program][IP_FIELD][1] != (MY_IP, MY_PORT):
                print(GREEN, "Going to kill remotely ", program, ENDC)
                # send request to runtime where the thread has migrated
                message = ("kill", program)
                sock.sendto(str(message).encode(), program_dictionary[program][IP_FIELD][1])
            print(GREEN, "Going to kill locally ", program, ENDC)
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
                if program_dictionary[key][IP_FIELD][1] == (MY_IP, MY_PORT):
                    if program_dictionary[key][STATE_FIELD] == READY:
                        dealWithReady(key)
                    else:
                        print(YELLOW, key, " is NOT running", ENDC)
                else:
                    print(BLUE, "\n\n\nThis thread has migrated...", ENDC)
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
            if program_dictionary[key][IP_FIELD][0] != (MY_IP, MY_PORT):
                print("This runtime is not my birth runtime! Going to send the 'send request'")
                message2send = ("send", key, blockedInfo[1])
                sock.sendto(str(message2send).encode(), program_dictionary[key][IP_FIELD][0])
                setBlockedState(key, DELIVERING)
                return
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
            if program_dictionary[program][IP_FIELD][1] != (MY_IP, MY_PORT):
                message2send = ("receive", program, (program_dictionary[key][THREAD_FIELD][1], message))
                sock.sendto(str(message2send).encode(), program_dictionary[program][IP_FIELD][1])
            program_dictionary[program][BLOCKED_INFO_FIELD][RCV_BUFFER].append((program_dictionary[key][THREAD_FIELD][1], message))
            setBlockedState(key, DELIVERING)
        elif program_dictionary[key][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == DELIVERING:
            if program_dictionary[key][IP_FIELD][0] != (MY_IP, MY_PORT):
                print("The mother runtime is dealing with the DELIVERING state")
                return
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
                if program_dictionary[key][IP_FIELD][1] != (MY_IP, MY_PORT):
                    message2send = ("send_ready", key)
                    sock.sendto(str(message2send).encode(), program_dictionary[key][IP_FIELD][1])
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
                        # del buffer[message](
                        buffer.remove(message)
                        if program_dictionary[key][IP_FIELD][0] != (MY_IP, MY_PORT):
                            message2send = ("deliver", key, message)
                            sock.sendto(str(message2send).encode(), program_dictionary[key][IP_FIELD][0])
                        # set program_dictionary here
                        (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
                        program_dictionary[key] = (name, args, threadID, groupID, IP, READY, (0, 0, buffer), program_counter, instr_dict, labels_dict, var_dict)
                else:
                    if message2receive in buffer:
                        print("Got the message I wanted: ", message2receive)
                        # print(RED, "will del buffer[message] =", buffer[message2receive], ENDC)
                        # del buffer[message2receive]
                        buffer.remove(message2receive)
                        if program_dictionary[key][IP_FIELD][0] != (MY_IP, MY_PORT):
                            message2send = ("deliver", key, message)
                            sock.sendto(str(message2send).encode(), program_dictionary[key][IP_FIELD][0])
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
                    if program_dictionary[key][IP_FIELD][0] != (MY_IP, MY_PORT):
                        message2send = ("deliver", key, message)
                        sock.sendto(str(message2send).encode(), program_dictionary[key][IP_FIELD][0])
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
                        blockedType = program_dictionary[key][BLOCKED_INFO_FIELD][BLOCKED_TYPE]
                        if program_dictionary[key][IP_FIELD][1] == (MY_IP, MY_PORT) or blockedType == SENDING or blockedType == DELIVERING:
                            dealWithBlocked(key)
                        else:
                            print(BLUE, "\n\n\nThis thread has migrated...", ENDC)
                    elif program_dictionary[key][STATE_FIELD] == ENDED:
                        print(YELLOW, "Going to delete ", key, ENDC)
                        key2del = key
                        break
            if key2del >= 0:
                if program_dictionary[key2del][IP_FIELD][0] != (MY_IP, MY_PORT):
                    message2send = ("kill", key2del)
                    sock.sendto(str(message2send).encode(), program_dictionary[key2del][IP_FIELD][0])
                del program_dictionary[key2del]
            # print(GREEN, program_dictionary, ENDC)
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

def global_ids_update(sock, my_load):
    print("Going to inform others with", next_group_id, next_thread_id, my_load)
    message = ("inform", (next_group_id, next_thread_id, my_load))
    sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))

def migrate(group, thread, runtime2send2):
    # search for the runtime IP
    print(GREEN, other_runtimes_dict, ENDC)
    if runtime2send2 not in other_runtimes_dict:
        print("Runtime to send to was not found.")
        return
    else:
        print("I found the runtime to send program to.")

    program_dictionary_lock.acquire()
    foundProgram = False
    print("\n\n\n\n\n\n\nGoing to find the thread")
    for program in program_dictionary:
        print(program_dictionary[program][GROUP_FIELD], " - ", program_dictionary[program][THREAD_FIELD][1])
        if program_dictionary[program][GROUP_FIELD] == group and program_dictionary[program][THREAD_FIELD][1] == thread:
            print(BLUE, "Found the thread for migration", ENDC)
            foundProgram = True
            break
    if foundProgram == False:
        print("Program ", group, " - ", thread, " not found. Going to ignore this migration request.")
        program_dictionary_lock.release()
        return
    print("program_dictionary entry to send: ", program_dictionary[program])
    if program_dictionary[program][IP_FIELD][0] != (MY_IP, MY_PORT):
        print(GREEN, "I am not your biological father. We must inform him.", ENDC)
        message2send = ("biological_inform", program, runtime2send2)
        sock.sendto(str(message2send).encode(), program_dictionary[program][IP_FIELD][0])

    (name, args, threadID, groupID, (birthIP, _), state, blockedInfo, pc, instr, label, var) = program_dictionary[program]
    (blockedType, (sleepingStart, sleepingTime), msg_buffer) = blockedInfo
    if state == BLOCKED and blockedType == SLEEPING:
        sleepingStart += sleepingTime
    program_dictionary[program] = (name, args, threadID, groupID, (birthIP, runtime2send2), state, (blockedType, (sleepingStart, sleepingTime), msg_buffer), pc, instr, label, var)
    fragNsend(sock, program_dictionary[program], runtime2send2)
    if program_dictionary[program][IP_FIELD][0] != (MY_IP, MY_PORT):
        print(GREEN, "I am not your father so you are dead to me now.", ENDC)
        del program_dictionary[program]
    program_dictionary_lock.release()

class MulticastListener(Thread):
    def run(self):
        while True:
            global next_group_id
            global next_thread_id
            # init - receive IP from the other runtime
            d = mult_sock.recvfrom(UDP_SIZE)
            print("I received ", d[0].decode())
            # print((MY_IP, MY_PORT))
            # print(d[1])
            if d[1] == (MY_IP, MY_PORT):
                continue
            data = make_tuple(d[0].decode())
            if data[0] == "hello":
                print("New runtime @ ", d[1])
                ids_lock.acquire()
                other_runtimes_dict[d[1]] = 0
                # my_load: vres to apo program_dictionary
                program_dictionary_lock.acquire()
                print("\n\n\n", len(list(program_dictionary)), "\n\n")
                my_load = 0
                for program in program_dictionary:
                    if program_dictionary[program][IP_FIELD][1] == (MY_IP, MY_PORT):
                        my_load += 1
                print(my_load, "\n\n")
                program_dictionary_lock.release()
                print("Going to inform the one that just entered that:")
                print("next_group_id: ", next_group_id)
                print("next_thread_id: ", next_thread_id)
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

                program_dictionary_lock.acquire()
                for program in program_dictionary:
                    if program_dictionary[program][IP_FIELD][0] == d[1]:
                        print(GREEN, "Your father is dead. I will not support you!", ENDC)
                        setState(program, ENDED)
                    elif program_dictionary[program][IP_FIELD][1] == d[1]:
                        print(GREEN, "I am your biological father but your current dad is dead. So you are dead to me too.")
                        setState(program, ENDED)
                    else:
                        print(GREEN, "Shantay you stay", ENDC)
                program_dictionary_lock.release()
            elif data[0] == "inform":
                print("I was informed and I change my next_ids to", data[1])
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

                # ADD IN program_dictionary
                # 1) na pairnei to pedio tou threadID kai na to xrhsimopoiei ws key
                # 2) an uparxei sleep na prosarmozei ton xrono (h mhpws to runtime pou to stelnei?)
                program_dictionary[program_dictionary_entry[THREAD_FIELD][0]] = program_dictionary_entry
                # 3) na allaksoume tin IP (h mhpws to runtime pou to stelnei?)
            elif data[0] == "inform":
                ids_lock.acquire()
                next_group_id, next_thread_id, load = data[1]
                if d[1] not in other_runtimes_dict:
                    other_runtimes_dict[d[1]] = load
                    print(other_runtimes_dict)
                ids_lock.release()
            elif data[0] == "kill":
                print(YELLOW, data[1], ENDC)
                program_dictionary_lock.acquire()
                if data[1] in program_dictionary:
                    setState(data[1], ENDED)
                program_dictionary_lock.release()
            elif data[0] == "print":
                print(RED, "Group ", program_dictionary[data[1]][GROUP_FIELD], ", Thread ", program_dictionary[data[1]][THREAD_FIELD][1], ":", data[2], ENDC)
            elif data[0] == "receive": # from the migrated thread's perspective
                program_dictionary_lock.acquire()
                program_dictionary[data[1]][BLOCKED_INFO_FIELD][RCV_BUFFER].append(data[2])
                program_dictionary_lock.release()
            elif data[0] == "deliver":
                program_dictionary_lock.acquire()
                (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[data[1]]
                buffer = blockedInfo[2]
                buffer.remove(data[2])
                program_dictionary[data[1]] = (name, args, threadID, groupID, IP, READY, (0, 0, buffer), program_counter, instr_dict, labels_dict, var_dict)
                program_dictionary_lock.release()
            elif data[0] == "send":
                program_dictionary_lock.acquire()
                print(YELLOW, "I received the send request: ", data[2], ENDC)
                (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[data[1]]
                _, _, buffer = blockedInfo
                program_dictionary[data[1]] = (name, args, threadID, groupID, IP, BLOCKED, (SENDING, data[2], buffer), program_counter, instr_dict, labels_dict, var_dict)
                program_dictionary_lock.release()
            elif data[0] == "send_ready":
                program_dictionary_lock.acquire()
                setState(data[1], READY)
                program_dictionary_lock.release()
            elif data[0] == "biological_inform":
                program_dictionary_lock.acquire()
                (name, args, threadID, groupID, IP, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[data[1]]
                program_dictionary[data[1]] = (name, args, threadID, groupID, ((MY_IP, MY_PORT), data[2]), state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict)
                program_dictionary_lock.release()

################################################################################
# edw tha mpei to load balancing


################################################################################

# init private socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
MY_IP = get_IP()
MY_PORT = find_avl_port(sock, MY_IP)
print(MY_IP)
print(MY_PORT)

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

def print_menu():
    print("######### MENU #########")
    print("# run <prog>  <arg> ...<arg> ||<prog>  <arg> ... <arg> ||... ||<prog>  <arg> ... <arg>")
    print("# list")
    print("# kill <threadID> ... <threadID>")
    print("# migrate <groupID> <threadID> <IP address> <port>")
    print("# exit")
    # print("########################")

def user_interface():
    global next_group_id
    global next_thread_id

    programs2start = {}
    next_prgrm_id = 0

    while True:
        line = input("Enter command: ")
        if line == "":
            continue
        command_list = line.split()

        if   command_list[0] == 'run'    :  # done
            new_program = True
            programs2start = {}
            next_prgrm_id = 0
            ids_lock.acquire()
            for i in command_list[1:]:
                if i == '||':
                    argv_dict["$argc"] = argc
                    print("Going to check program ", program_name, " with args: ", argv_dict)
                    labels, instructions, error_code = parser(program_name)
                    if (error_code == FAIL):
                        print("syntax error. Going to ignore whole group")
                        next_thread_id -= len(list(programs2start.keys()))
                        ids_lock.release()
                        continue
                    programs2start[next_thread_id] = (program_name, (next_thread_id, next_prgrm_id), next_group_id, next_prgrm_id, argv_dict, instructions, labels)
                    next_thread_id += 1
                    next_prgrm_id += 1
                    new_program = True
                elif new_program:
                    new_program = False
                    program_name = i
                    argv_dict = {}
                    argv_dict["$arg0"] = program_name
                    argc = 1
                else:
                    argv_dict["$arg" + str(argc)] = i
                    argc += 1
            argv_dict["$argc"] = argc
            print("Going to check program ", program_name, " with args: ", argv_dict)
            labels, instructions, error_code = parser(program_name)
            if (error_code == FAIL):
                print("Syntax Error. Going to ignore whole group")
                next_thread_id -= len(list(programs2start.keys()))
                continue
            programs2start[next_thread_id] = (program_name, (next_thread_id, next_prgrm_id), next_group_id, next_prgrm_id, argv_dict, instructions, labels)
            next_thread_id += 1
            next_group_id += 1
            for program2start in programs2start:
                print("Going to start, ", program2start)
                # add in the program_dictionary
                name, threadID, groupID, programID, argvs, instr_dict, labels_dict = programs2start[program2start]
                program_dictionary[program2start] = (name, argvs, threadID, groupID, ((MY_IP, MY_PORT),(MY_IP, MY_PORT)), READY, (0,(0,0),[]), 0, instr_dict, labels_dict, {})
            global_ids_update(sock, len(list(program_dictionary)))
            ids_lock.release()
        elif command_list[0] == 'list'   :  # done
            print("next_group_id: ", next_group_id)
            print("next_thread_id: ", next_thread_id)
            print("Programs:")
            if not program_dictionary:
                print("(None)")
                continue
            for program in program_dictionary:
                if program_dictionary[program][IP_FIELD][0] != (MY_IP, MY_PORT):
                    print("This program does not belong to me")
                    # continue
                print_message  = str(program_dictionary[program][IP_FIELD]) + " running: "
                print_message += "Thread " + str(program_dictionary[program][THREAD_FIELD]) + ", group " + str(program_dictionary[program][GROUP_FIELD]) + ", executing " + str(program_dictionary[program][NAME_FIELD]) + ": "
                if   program_dictionary[program][STATE_FIELD] == RUNNING:
                    print_message += "running."
                elif program_dictionary[program][STATE_FIELD] == READY:
                    print_message += "ready to run."
                elif program_dictionary[program][STATE_FIELD] == ENDED:
                    print_message += "dead."
                elif program_dictionary[program][STATE_FIELD] == BLOCKED:
                    print_message += "blocked because it's "
                    if program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == SLEEPING:
                        print_message += "sleeping."
                    elif program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == RECEIVING:
                        print_message += "waiting for a message."
                    elif program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == SENDING:
                        print_message += "sending a message."
                    elif program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == DELIVERING:
                        print_message += "delivering a message."
                    else:
                        print_message += "??"
                else:
                    print_message += "???"
                print(print_message)
        elif command_list[0] == 'kill'   :  # done
            program_dictionary_lock.acquire()
            kill(command_list[1])
            program_dictionary_lock.release()
        elif command_list[0] == 'menu'   :  # done
            print_menu()
        elif command_list[0] == 'migrate':
            if len(command_list) != 5:
                print("Wrong number of arguments: migrate <groupID> <threadID> <IP address> <port>")
                continue

            runtime2send2 = (command_list[3],int(command_list[4]))
            groupID = int(command_list[1])
            programID = int(command_list[2])
            migrate(groupID, programID, runtime2send2)
        elif command_list[0] == 'exit'   :  # done
            print("Exiting...")
            message = ("exit", 0)
            sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))
            exit()
        else:
            print("Unknown command!")
        print("########################")
##########################################

user_interface()
