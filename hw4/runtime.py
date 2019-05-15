import time
import threading
from threading import Thread
from threading import Lock
# from user_interface import user_interface

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

def increment_pc(key):
    global program_dictionary
    global program_dictionary_lock
    print("going to increment pc")
    (name, args, threadID, groupID, programID, state, blockedInfo, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, threadID, groupID, programID, state, blockedInfo, program_counter+1, instr_dict, labels_dict, var_dict)

def dealWithReady(key):
    global program_dictionary
    global program_dictionary_lock

    setState(key, RUNNING)
    print(YELLOW, key, " is running", ENDC)
    for i in range(INSTR_TIME_ON_CPU):

        print(YELLOW, "running command", ENDC)
        # run command
        # setSleep(key, 5)       # debugging stuff
        if i == 2:               # debugging stuff
            setReceive(key, 1)   # debugging stuff

        # increment program counter
        increment_pc(key)

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
instr_dict = {}
labels_dict = {}
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
