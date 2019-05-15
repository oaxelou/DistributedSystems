import sys
var_dict = {}
label_dict = {}
varcnt = 0

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
    global var_dict
    global varcnt
    # expects Var VarVal

    if len(args) != 2:
        return -1
    elif args[0][0] != '$':
        return -1
    elif args[1][0] != '$' and args[1].isdigit()==False and (args[1][0] != '\"' or args[1][len(args[1])-1] != '\"'):
        return -1
    else:
        var_dict[varcnt] = args[0]
        varcnt += 1
        if args[1][0] == '$':
            var_dict[varcnt] = args[1]
            varcnt += 1

        return 0

def check_for_arithmetic(args):
    global var_dict
    global varcnt
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
        var_dict[varcnt] = args[0]
        varcnt += 1
        for i in range(1,2):
            if args[i][0] == '$':
                var_dict[varcnt] = args[i]
                varcnt += 1
        return 0

def check_for_branch(args):
    global label_dict
    global var_dict
    global varcnt
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
        for i in range(0,1):
            if args[i][0] == '$':
                var_dict[varcnt] = args[i]
                varcnt += 1
        return 0

def check_for_csp(args):
    global var_dict
    global varcnt
    # should have at least two arguments
    if len(args) < 2:
        return -1
    for i in range(len(args)):
        if args[i][0] != '$' and args[i].isdigit()==False and (args[i][0] != '\"' or args[i][len(args[i])-1] != '\"'):
            return -1
        else:
            if args[i][0] == '$':
                var_dict[varcnt] = args[i]
                varcnt += 1
    return 0

def check_for_BRA(args):
    if len(args) != 1:
        return -1
    elif args[0][0] != '#':
        return -1
    else:
        return 0

def check_for_SLP(args):
    global var_dict
    global varcnt
    if len(args) != 1:
        return -1
    elif args[0][0] != '$' and args[0].isdigit()==False:
        return -1
    else:
        if args[0][0] == '$':
            var_dict[varcnt] = args[0]
            varcnt += 1
        return 0

def check_for_PRN(args):
    global var_dict
    global varcnt
    # should have at least one argument
    if len(args) < 1:
        return -1
    for i in range(len(args)):
        if args[i][0] != '$' and args[i].isdigit()==False and (args[i][0] != '\"' or args[i][len(args[i])-1] != '\"'):
            return -1
        else:
            if args[i][0] == '$':
                var_dict[varcnt] = args[i]
                varcnt += 1
    return 0

def check_for_RET(args):
    if len(args) != 0:
        return -1
    else:
        return 0
############################ main ############################


f = open(sys.argv[1])
instr_list = f.readlines()
# edw to f mporei na kleisei, den to xreiazomaste allo
f.close()

print(instr_list)

instr_dict = {}

instcnt = 0

for item in instr_list:
    instr_dict[instcnt] = item.split()
    first_word = instr_dict[instcnt][0]
    args = instr_dict[instcnt][1:]
    # print(args)
    if first_word[0] == '#':
        print("label is: ", first_word)
        # found a label
        label_dict[first_word] = instcnt
        # print("\nIN LABELS:", instr_dict[instcnt][0], "\n")
        del instr_dict[instcnt][0]
        # print("\nIN LABELS:", instr_dict[instcnt], "\n")

    instcnt += 1


instcnt = 0
for item in instr_list:
    print("opcode is: ", instr_dict[instcnt][0])
    opcode = instr_dict[instcnt][0]
    args = instr_dict[instcnt][1:]

    # check what group the command belongs to
    # if it not one of the allowed commands, command_Group
    # returns -1 and the parser terminates
    if op_group(opcode) == -1:
        print("wrong operation")
        # exit()
    elif op_group(opcode) == 0:
        if check_for_SET(args) == -1:
            print("SET expects: Var VarVal")
            exit()
    elif op_group(opcode) == 1:
        if check_for_arithmetic(args) == -1:
            print("arithmetic ops expect: Var VarVal1 VarVal2")
            exit()
    elif op_group(opcode) == 2:
        if check_for_branch(args) == -1:
            print("branch operations expect: VarVal1 VarVal2 Label")
            exit()
    elif op_group(opcode) == 3:
        if check_for_csp(args) == -1:
            print("SND/RCV operations expect: VarVal, {VarVal}")
            exit()
    elif op_group(opcode) == 4:
        if check_for_SLP(args) == -1:
            print("SLP expects: VarVal")
            exit()
    elif op_group(opcode) == 5:
        if check_for_PRN(args) == -1:
            print("PRN expects: {VarVal}")
            exit()
    elif op_group(opcode) == 6:
        if check_for_RET(args) == -1:
            print("RET expects no args")
            exit()
    elif op_group(opcode) == 7:
        if check_for_BRA(args) == -1:
            print("BRA expects: Label")
            exit()
    else:
        print("sth went wrong, should not be here")

    instcnt += 1

for item in instr_dict:
    print(instr_dict[item])

print(label_dict)
print(var_dict)
