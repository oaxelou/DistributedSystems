from user import *


class Receiver(Thread):
    def run(self):
        while 1:
            time.sleep(0.1)
            # print("Message buckets:")
            for group_id in groups_dict:
                while 1:
                    (msg_type, msg) = grp_recv(group_id)
                    if msg_type == GM_MSG_CODE:
                        print(groups_dict[group_id], ": ", YELLOW, msg, ENDC)
                    elif msg_type == USER_MSG_CODE:
                        print(groups_dict[group_id], ": ", BLUE, msg, ENDC)
                    else:
                        break
################################################################################

groups_no = int(input("Enter number of groups you want to enter: "))
groups_dict = {}
for i in range(groups_no):
    gname = input("Name of "+ str(i) + "th group: ")
    g_id = join(gname, sys.argv[1])
    print("Group id: ", g_id)
    groups_dict[g_id] = gname
# gsock_id_1 = join("g1", sys.argv[1])
# gsock_id_2 = join("g2", sys.argv[1])
if -1 in groups_dict:
    print("Error joining the groups!")
    exit()

input("Press enter to start communication: ")

receiveThread = Receiver()
receiveThread.daemon = True
receiveThread.start()

try:
    while 1:
        try:
            grp_id = int(input("Group id: "))
        except ValueError:
            print("not valid grp_id")
            continue
        if grp_id not in groups_dict:
            print(grp_id, "not in groups_dict.")
            continue
        msg = input("Message: ")
        grp_send(grp_id, msg)
        # for group_id in groups_dict:
        #     grp_send(group_id, input("Send message to group" + str(group_id) + ":"))
except :
    print("!")

print("Going to leave")
for group_id in groups_dict:
    leave(group_id)
