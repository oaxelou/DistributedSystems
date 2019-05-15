import time
import threading
from threading import Thread
from threading import Lock


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

######## FIELD DEFINES #######
NOT_BLOCKED = 0
SLEEPING = 1
RECEIVING = 2

######## FIELD DEFINES #######
NAME_FIELD = 0
ARGS_FIELD = 1
GROUP_FIELD = 2
STATE_FIELD = 3
BLOCKED_INFO_FIELD = 4
PC_FIELD = 5
INSTR_FIELD = 6
LABEL_FIELD = 7
VAR_FIELD = 8

######## FIELD DEFINES #######
INSTR_TIME_ON_CPU = 5

################# CLASSES #################
class UserCommunicationThread(Thread):
    def run(self):
        pass

def setSleep(key, interval):
    global program_dictionary
    global program_dictionary_lock
    print("Going to sleep for ", interval, "secs")
    (name, args, group, _, _, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, group, BLOCKED, (SLEEPING, (time.time(), interval)), program_counter, instr_dict, labels_dict, var_dict)


def setState(key, newState):
    global program_dictionary
    global program_dictionary_lock
    print("Going to set ", key, " to ", newState)
    (name, args, group, _, _, program_counter, instr_dict, labels_dict, var_dict) = program_dictionary[key]
    program_dictionary[key] = (name, args, group, newState, 0, program_counter, instr_dict, labels_dict, var_dict)

def dealWithReady(key):
    global program_dictionary
    global program_dictionary_lock

    setState(key, RUNNING)
    print(YELLOW, key, " is running", ENDC)
    for i in range(INSTR_TIME_ON_CPU):
        print(YELLOW, "running command", ENDC)
        # run command
        # setSleep(key, 5)

        if i == 2:
            setSleep(key, 5)
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
        if program_dictionary[key][BLOCKED_INFO_FIELD][1] != 0:
            print("Message has been received: ", program_dictionary[key][BLOCKED_INFO_FIELD][1])
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
group = 0
state = READY
blocked_info = 0 #(SLEEPING,(time.time(), 3)) # useful only when blocked
program_counter = 0
instr_dict = {}
labels_dict = {}
var_dict = {}

program_dictionary[0] = (name, args, group, state, blocked_info, program_counter, instr_dict, labels_dict, var_dict)
program_dictionary_lock.release()


time.sleep(3)

# program_dictionary_lock.acquire()
# program_dictionary[0] = (name, args, group, ENDED, 0, program_counter, instr_dict, labels_dict, var_dict)
# program_dictionary_lock.release()





time.sleep(10)
exit()
