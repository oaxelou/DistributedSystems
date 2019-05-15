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
from runtime import *

def print_menu():
    print("######### MENU #########")
    print("# run <prog>  <arg> ...<arg> ||<prog>  <arg> ... <arg> ||... ||<prog>  <arg> ... <arg>")
    print("# list")
    print("# kill <threadID> ... <threadID>")
    print("# exit")
    # print("########################")

def user_interface():
    programs2start = {}

    next_group_id = 0
    next_thread_id = 0
    next_prgrm_id = 0

    while True:
        line = input("Enter command: ")
        command_list = line.split()

        if command_list[0] == 'run':
            new_program = True
            programs2start = {}
            next_prgrm_id = 0
            for i in command_list[1:]:
                if i == '||':
                    # print("Going to start program ", program_name, " with args: ", arg_list)
                    programs2start[next_thread_id] = (program_name, next_thread_id, next_group_id, next_prgrm_id, (len(arg_list), arg_list))
                    next_thread_id += 1
                    next_prgrm_id += 1
                    new_program = True
                elif new_program:
                    new_program = False
                    program_name = i
                    arg_list = []
                else:
                    arg_list.append(i)
            # print("Going to start program ", program_name, " with args: ", arg_list)
            programs2start[next_thread_id] = (program_name, next_thread_id, next_group_id, next_prgrm_id, (len(arg_list), arg_list))
            next_thread_id += 1
            next_group_id += 1
            for program2start in programs2start.values():
                print("Going to start, ", program2start)
        elif command_list[0] == 'list':
            print("Going to print list with programs running")
            print(program_dictionary)
        elif command_list[0] == 'kill':
            for i in command_list[1:]:
                print("Going to kill ", i)
        elif command_list[0] == 'menu':
            print_menu()
        elif command_list[0] == 'exit':
            print("Exiting...")
            exit()
        else:
            print("Unknown command!")
        print("########################")
##########################################

user_interface()
