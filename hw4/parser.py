import sys

label_dict = {}
SUCCESS = 0
FAIL = -1

def op_group(operation):
    arithmetic = ["ADD", "SUB", "MUL", "DIV", "MOD"]
    branch = ["BGT", "BGE", "BLT", "BLE", "BEQ"]
    csp = ["SND", "RCV"]

    if operation == "SET":
        return 0
    elif operation in arithmetic:
        return 1
    elif operation in branch:
        return 2
    elif operation in csp:
        return 3
    elif operation == "SLP":
        return 4
    elif operation == "PRN":
        return 5
    elif operation == "RET":
        return 6
    elif operation == "BRA":
        return 7
    else:
        return -1

def check_for_SET(args):
    # expects Var VarVal
    if len(args) != 2:
        return -1
    elif args[0][0] != '$':
        return -1
    elif args[1][0] != '$' and args[1].isdigit()==False and (args[1][0] != '\"' or args[1][len(args[1])-1] != '\"'):
        return -1
    else:
        return 0

def check_for_arithmetic(args):
    # arithmetic ops expect: Var VarVal1 VarVal2
    if len(args) != 3:
        return -1
    elif args[0][0] != '$':
        return -1
    elif args[1][0] != '$' and args[1].isdigit()==False:
        return -1
    elif args[2][0] != '$' and args[2].isdigit()==False:
        return -1
    else:
        return 0

def check_for_branch(args):
    global label_dict
    # branch operations expect: VarVal1 VarVal2 Label
    if len(args) != 3:
        return -1
    elif args[0][0] != '$' and args[0].isdigit()==False:
        return -1
    elif args[1][0] != '$' and args[1].isdigit()==False:
        return -1
    elif args[2][0] != '#':
        return -1
    # check if label exists in label_dict
    elif args[2] not in label_dict:
        print("wrong label")
        return -1
    else:
        return 0

def check_for_csp(args):
    # should have at least two arguments
    if len(args) < 2:
        return -1
    for i in range(len(args)):
        if args[i][0] != '$' and args[i].isdigit()==False and (args[i][0] != '\"' or args[i][len(args[i])-1] != '\"'):
            return -1
    return 0

def check_for_BRA(args):
    if len(args) != 1:
        return -1
    elif args[0][0] != '#':
        return -1
    else:
        return 0

def check_for_SLP(args):
    if len(args) != 1:
        return -1
    elif args[0][0] != '$' and args[0].isdigit()==False:
        return -1
    else:
        return 0

def check_for_PRN(args):
    # should have at least one argument
    if len(args) < 1:
        return (-1,0)

    print("PRINT: OLD ARGS: ")
    print(args)
    new_args = []
    arg_iter = 0
    while arg_iter < len(args):
        # print(args[arg_iter])
        if args[arg_iter][0] == '\"':
            if args[arg_iter][len(args[arg_iter])-1] == '\"' and len(args[arg_iter]) != 1:
                new_args.append(args[arg_iter])
                arg_iter += 1
                continue
            if arg_iter == len(args)-1:
                print("Syntax Error. The string should ed somewhere")
            for remaining in range(arg_iter+1, len(args)):
                if remaining == len(args) - 1 and args[remaining][len(args[remaining])-1] != '\"':
                    print("Syntax error. string is not ending somewhere")
                    return -1,0
                args[arg_iter] += " "
                args[arg_iter] += args[remaining]
                if args[remaining][len(args[remaining])-1] == '\"':
                    break
            new_args.append(args[arg_iter])
            arg_iter = remaining + 1
        elif args[arg_iter][0] == '$':
            new_args.append(args[arg_iter])
            arg_iter += 1
        elif args[arg_iter].isdigit():
            new_args.append(args[arg_iter])
            arg_iter += 1
        else:
            print("Syntax Error")
            return -1,0

    # args = new_args
    # print("new:", args)
    for iter in range(len(new_args)):
        # print(args[iter])
        args[iter] = new_args[iter]
    # for rest in range(iter, len(args)-1):
        # del args[rest]
    print("PRINT NEW ARGS: ")
    print(args)
    # concatenation of strings
    # for i in range(len(args)):
    #     if args[i][0] != '$' and args[i].isdigit()==False and (args[i][0] != '\"' or args[i][len(args[i])-1] != '\"'):
    #         return -1
    return (0,args)

def check_for_RET(args):
    if len(args) != 0:
        return -1
    else:
        return 0
############################ main ############################

def parser(program_name):
    try:
        f = open(program_name)
        instr_list = f.readlines()
        print(instr_list)
        # edw to f mporei na kleisei, den to xreiazomaste allo
        f.close()
    except FileNotFoundError:
        print("No such file: ", program_name)
        return (0,0,-1)
    # print(instr_list)

    instr_dict = {}
    instcnt = 0

    print(instr_list[0])
    if instr_list[0] != "#SIMPLESCRIPT\n":
        print("The code for this type of program not found!")
        exit()
    else:
        print("I recognized this program type")

    instr_list = instr_list[1:]
    for item in instr_list:
        instr_dict[instcnt] = item.split()
        first_word = instr_dict[instcnt][0]
        args = instr_dict[instcnt][1:]
        # print(args)
        if first_word[0] == '#':
            # print("label is: ", first_word)
            # found a label
            label_dict[first_word] = instcnt
            # print("\nIN LABELS:", instr_dict[instcnt][0], "\n")
            del instr_dict[instcnt][0]
            # print("\nIN LABELS:", instr_dict[instcnt], "\n")

        instcnt += 1


    instcnt = 1
    while instcnt < len(list(instr_list)):
        print("opcode is: ", instr_dict[instcnt][0])
        opcode = instr_dict[instcnt][0]
        args = instr_dict[instcnt][1:]

        # check what group the command belongs to
        # if it not one of the allowed commands, command_Group
        # returns -1 and the parser terminates
        if op_group(opcode) == -1:
            print("wrong operation")
            return(0,0,FAIL)
        elif op_group(opcode) == 0:
            if check_for_SET(args) == -1:
                print("SET expects: Var VarVal")
                return(0,0,FAIL)
        elif op_group(opcode) == 1:
            if check_for_arithmetic(args) == -1:
                print("arithmetic ops expect: Var VarVal1 VarVal2")
                return(0,0,FAIL)
        elif op_group(opcode) == 2:
            if check_for_branch(args) == -1:
                print("branch operations expect: VarVal1 VarVal2 Label")
                return(0,0,FAIL)
        elif op_group(opcode) == 3:
            if check_for_csp(args) == -1:
                print("SND/RCV operations expect: VarVal, {VarVal}")
                return(0,0,FAIL)
        elif op_group(opcode) == 4:
            if check_for_SLP(args) == -1:
                print("SLP expects: VarVal")
                return(0,0,FAIL)
        elif op_group(opcode) == 5:
            returnvalue, new_args = check_for_PRN(args)
            if returnvalue == -1:
                print("PRN expects: {VarVal}")
                return(0,0,FAIL)
            instr_dict[instcnt][1:] = new_args

        elif op_group(opcode) == 6:
            if check_for_RET(args) == -1:
                print("RET expects no args")
                return(0,0,FAIL)
            else:
                break
        elif op_group(opcode) == 7:
            if check_for_BRA(args) == -1:
                print("BRA expects: Label")
                return(0,0,FAIL)
        else:
            print("sth went wrong, should not be here")

        instcnt += 1

    for item in instr_dict:
        print(instr_dict[item])
    #
    print(label_dict)
    print(instr_dict)

    return (label_dict, instr_dict, SUCCESS)

##### main #####
# labels, instructions, error_code = parser(sys.argv[1])
# if (error_code == FAIL):
#     print("syntax error")
#     print(error_code)
#     exit()
#
# print(labels)
# for instr_num, instr in instructions.items():
#     print(instr_num, ": ", instr)
