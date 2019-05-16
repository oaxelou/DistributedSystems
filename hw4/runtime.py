import time
import threading
from threading import Thread
from threading import Lock
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

######## FIELD DEFINES #######
NAME_FIELD = 0
ARGS_FIELD = 1
THREAD_FIELD = 2
GROUP_FIELD = 3
PROGRAM_FIELD = 4
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
    (name, args, threadID, groupID, programID, _, _, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, threadID, groupID, programID, BLOCKED, (SLEEPING, (time.time(), interval)), program_counter, instr_dict, labels_dict, var_dict)

def setReceive(key, sender): # block because of waiting for a message
    global program_dictionary
    global program_dictionary_lock
    print("Going to wait for a message from ", sender)
    (name, args, threadID, groupID, programID, _, _, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, threadID, groupID, programID, BLOCKED, (RECEIVING, (sender, 0)), program_counter, instr_dict, labels_dict, var_dict)

def setDeliver(key, receiver, message): # set message to blocked
    global program_dictionary
    global program_dictionary_lock
    print("Going to deliver message to ", receiver)
    if receiver not in program_dictionary:
        print("There is no program with id: ", receiver)
        exit() # not exit but for simplicity
    (name, args, threadID, groupID, programID, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[receiver]
    if state != BLOCKED:
        print("There is no blocked program with id: ", receiver)
        exit() # not exit but for simplicity
    (blockType, (sender, old_message)) = blockedInfo
    if blockType != RECEIVING:
        print("Not waiting for a message.")
        exit()
    if old_message != 0:
        print("Already got the message!")
        exit()
    if sender != key:
        print("The blocked thread is not waiting for a message from ", key)
        exit() # not exit but for simplicity
    program_dictionary[receiver] = (name, args, threadID, groupID, programID, BLOCKED, (RECEIVING, (sender, message)), program_counter, instr_dict, labels_dict, var_dict)

def setState(key, newState):
    global program_dictionary
    global program_dictionary_lock
    print("Going to set ", key, " to ", newState)
    (name, args, threadID, groupID, programID, _, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, threadID, groupID, programID, newState, blockedInfo, program_counter, instr_dict, labels_dict, var_dict)

def increment_pc(key, new_pc):
    global program_dictionary
    global program_dictionary_lock
    print("going to increment pc")
    (name, args, threadID, groupID, programID, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, threadID, groupID, programID, state, blockedInfo, new_pc, instr_dict, labels_dict, var_dict)

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
    # local_vars = program_dictionary[key][VAR_FIELD]

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

        if check_varval_int(command[3], key) == 'var':
            varval2 = program_dictionary[key][VAR_FIELD][command[3]]
        elif check_varval_int(command[3], key) == 'val':
            varval2 = int(command[3])
        else:
            print(command[3], "not defined")


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

        if check_varval_int(command[2], key) == 'var':
            varval2 = program_dictionary[key][VAR_FIELD][command[2]]
        elif check_varval_int(command[2], key) == 'val':
            varval2 = int(command[2])
        else:
            print(command[2], "not defined")

        # at this point we know that the label we want to jump to exists
        # find label in labels_dict and change program counter
        # labels are in program_dictionary[key][LABEL_FIELD]

        new_pc = program_dictionary[key][LABEL_FIELD][command[3]]

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
        new_pc = program_dictionary[key][LABEL_FIELD][command[1]]
        return new_pc

    elif command[0] == 'SLP':
        # varval1 = command[1]

        if check_varval_int(command[1], key) == 'var':
            varval1 = program_dictionary[key][VAR_FIELD][command[1]]
        elif check_varval_int(command[1], key) == 'val':
            varval1 = int(command[1])
        else:
            print(command[1], "not defined")

        setSleep(key, varval1)

    elif command[0] == 'PRN':
        for arg in command[1:]:
            if arg[0] == '$' and arg not in program_dictionary[key][VAR_FIELD]:
                print(arg, "not defined")
            else:
                print(RED, arg, ENDC)

    elif command[0] == 'RET':
        setState(key, ENDED)

    # unless there is a jump, return -1 aka NORMAL_PC_INCR
    return NORMAL_PC_INCR


def dealWithReady(key):
    global program_dictionary
    global program_dictionary_lock

    setState(key, RUNNING)
    print(YELLOW, key, " is running", ENDC)
    for i in range(INSTR_TIME_ON_CPU):

        print(YELLOW, "running command", ENDC)


        pc = program_dictionary[key][PC_FIELD]
        command = instr_dict[pc]

        # returns -1 if there is no branch
        new_pc = run_command(key, command)
        print("after run command: command =", command[0], "new_pc == ", new_pc)
        print(program_dictionary[key][VAR_FIELD])
        # run command
        # setSleep(key, 5)       # debugging stuff
        if i == 2:               # debugging stuff
            setReceive(key, 1)   # debugging stuff

        # increment program counter
        if new_pc == NORMAL_PC_INCR:
            increment_pc(key, pc+1)
        elif new_pc == UNDEFINED_VAR:
            # kill program and its group
            pass
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
        if program_dictionary[key][BLOCKED_INFO_FIELD][1][1] != 0:
            print("Message has been received: ", program_dictionary[key][BLOCKED_INFO_FIELD][1][1])
            setState(key, READY)
        else:
            print("Message has not been received yet")

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
                    print(RED, "Going to delete ", key, ENDC)
                    key2del = key
                    break

            if key2del >= 0:
                del program_dictionary[key2del]
                # else:
                #     print("Program ", key, " is not blocked. Going to try for another one")
            print(BLUE, program_dictionary, ENDC)
            program_dictionary_lock.release()
            time.sleep(1)
###########################################
next_group_id  = 0
next_thread_id = 0

blockedManager = BlockedManagerThread()
blockedManager.daemon = True
blockedManager.start()

interpreter = InterpreterThread()
interpreter.daemon = True
interpreter.start()

# Add a program in the program_dictionary
program_dictionary_lock.acquire()
name = "hello.c"
argc, argv = 1, (name)
args = (argc, argv)
threadID = 0
groupID = 0
programID = 0
state = READY
blocked_info = 0 #(SLEEPING,(time.time(), 3)) # useful only when blocked
program_counter = 0
instr_dict = {0: ['BRA', '#lm'], 1: ['ADD', '$rr', '4', '3'], 2: ['SLP', '10'], 3: ['SUB', '$rv', '10', '1'], \
                4: ['ADD', '$rr', '4', '0'], 5: ['SUB', '$rv', '10', '0'], 6: ['ADD', '$rr', '0', '0'], 7: ['SUB', '$rv', '10', '5']}

instr_dict = {0: ['PRN', '56', '"STRANG"'], 1: ['RET']}
labels_dict = {'#lm': 2}
var_dict = {}

program_dictionary[0] = (name, args, threadID, groupID, programID, state, blocked_info, program_counter, instr_dict, labels_dict, var_dict)
program_dictionary_lock.release()


time.sleep(3)

program_dictionary_lock.acquire()
setDeliver(1, 0, "hi")
# program_dictionary[0] = (name, args, group, ENDED, 0, program_counter, instr_dict, labels_dict, var_dict)
program_dictionary_lock.release()





# time.sleep(10)
# exit()
