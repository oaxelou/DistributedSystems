# Check nested dictionaries

# my_dict = {}
# my_dict[0] = ("hi.c", {})
#
# print(my_dict)
#
# name, instr_dict = my_dict[0]
# instr_dict[0] = ["ADD", "$res", "$var1", "$var2"]
# print(my_dict)

################################################################################
# User Intrface
# from runtime import *
# from parser import *
def print_menu():
    print("######### MENU #########")
    print("# run <prog>  <arg> ...<arg> ||<prog>  <arg> ... <arg> ||... ||<prog>  <arg> ... <arg>")
    print("# list")
    print("# kill <threadID> ... <threadID>")
    print("# migrate <groupID> <threadID> <IP address> <port>")
    print("# exit")
    # print("########################")

def user_interface():
    # global next_group_id
    # global next_thread_id
    #
    # programs2start = {}
    # next_prgrm_id = 0

    print("Obsolete file. Run directly <runtime.py> !")
    exit()
#     while True:
#         line = input("Enter command: ")
#         if line == "":
#             continue
#         command_list = line.split()
#
#         if   command_list[0] == 'run'    :  # done
#             new_program = True
#             programs2start = {}
#             next_prgrm_id = 0
#             for i in command_list[1:]:
#                 if i == '||':
#                     argv_dict["$argc"] = argc
#                     print("Going to check program ", program_name, " with args: ", argv_dict)
#                     labels, instructions, error_code = parser(program_name)
#                     if (error_code == FAIL):
#                         print("syntax error. Going to ignore whole group")
#                         continue
#                     programs2start[next_thread_id] = (program_name, (next_thread_id, next_prgrm_id), next_group_id, next_prgrm_id, argv_dict, instructions, labels)
#                     next_thread_id += 1
#                     next_prgrm_id += 1
#                     new_program = True
#                 elif new_program:
#                     new_program = False
#                     program_name = i
#                     argv_dict = {}
#                     argv_dict["$arg0"] = program_name
#                     argc = 1
#                 else:
#                     argv_dict["$arg" + str(argc)] = i
#                     argc += 1
#             argv_dict["$argc"] = argc
#             print("Going to check program ", program_name, " with args: ", argv_dict)
#             labels, instructions, error_code = parser(program_name)
#             if (error_code == FAIL):
#                 print("Syntax Error. Going to ignore whole group")
#                 next_thread_id -= len(list(programs2start.keys()))
#                 continue
#             programs2start[next_thread_id] = (program_name, (next_thread_id, next_prgrm_id), next_group_id, next_prgrm_id, argv_dict, instructions, labels)
#             next_thread_id += 1
#             next_group_id += 1
#             for program2start in programs2start:
#                 print("Going to start, ", program2start)
#                 # add in the program_dictionary
#                 name, threadID, groupID, programID, argvs, instr_dict, labels_dict = programs2start[program2start]
#                 program_dictionary[program2start] = (name, argvs, threadID, groupID, ((MY_IP, MY_PORT),(MY_IP, MY_PORT)), READY, (0,(0,0),[]), 0, instr_dict, labels_dict, {})
#             global_ids_update(sock, len(list(program_dictionary)))
#         elif command_list[0] == 'list'   :  # done
#             print("next_group_id: ", next_group_id)
#             print("next_thread_id: ", next_thread_id)
#             print("Programs:")
#             if not program_dictionary:
#                 print("(None)")
#                 continue
#             for program in program_dictionary:
#                 if program_dictionary[program][IP_FIELD][0] != (MY_IP, MY_PORT):
#                     print("This program does not belong to me")
#                     # continue
#                 print_message  = str(program_dictionary[program][IP_FIELD]) + " running: "
#                 print_message += "Thread " + str(program_dictionary[program][THREAD_FIELD]) + ", group " + str(program_dictionary[program][GROUP_FIELD]) + ", executing " + str(program_dictionary[program][NAME_FIELD]) + ": "
#                 if   program_dictionary[program][STATE_FIELD] == RUNNING:
#                     print_message += "running."
#                 elif program_dictionary[program][STATE_FIELD] == READY:
#                     print_message += "ready to run."
#                 elif program_dictionary[program][STATE_FIELD] == ENDED:
#                     print_message += "dead."
#                 elif program_dictionary[program][STATE_FIELD] == BLOCKED:
#                     print_message += "blocked because it's "
#                     if program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == SLEEPING:
#                         print_message += "sleeping."
#                     elif program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == RECEIVING:
#                         print_message += "waiting for a message."
#                     elif program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == SENDING:
#                         print_message += "sending a message."
#                     elif program_dictionary[program][BLOCKED_INFO_FIELD][BLOCKED_TYPE] == DELIVERING:
#                         print_message += "delivering a message."
#                     else:
#                         print_message += "??"
#                 else:
#                     print_message += "???"
#                 print(print_message)
#         elif command_list[0] == 'kill'   :  # done
#             program_dictionary_lock.acquire()
#             kill(command_list[1])
#             program_dictionary_lock.release()
#         elif command_list[0] == 'menu'   :  # done
#             print_menu()
#         elif command_list[0] == 'migrate':
#             if len(command_list) != 5:
#                 print("Wrong number of arguments: migrate <groupID> <threadID> <IP address> <port>")
#                 continue
#
#             runtime2send2 = (command_list[3],int(command_list[4]))
#             groupID = int(command_list[1])
#             programID = int(command_list[2])
#             migrate(groupID, programID, runtime2send2)
#         elif command_list[0] == 'exit'   :  # done
#             print("Exiting...")
#             message = ("exit", 0)
#             sock.sendto(str(message).encode(), (MCAST_GRP, MCAST_PORT))
#             exit()
#         else:
#             print("Unknown command!")
#         print("########################")
# ##########################################

user_interface()
