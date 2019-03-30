from user import *

MESSAGE_BATCH = 100
class Receiver(Thread):
    def run(self):
        global g_id
        msg_no = 0
        print(g_id)
        while 1:
            # time.sleep(1)
            # print("Message buckets:")
            (msg_type, msg) = grp_recv(g_id)
            if msg_type == GM_MSG_CODE:
                print("testingGroup: ", YELLOW, msg, ENDC)
            elif msg_type == USER_MSG_CODE:
                if sys.argv[1] != "sender":
                    print("testingGroup: ", BLUE, msg, ENDC)
                if sys.argv[1] == "sender":
                    if msg == "not_sender: catch'em all":
                        print("Time elapsed for ", MESSAGE_BATCH, "messages: ", time.time() - start_time)
                        print("EVERYONE GOT WHAT THEY DESERVED")
                        break
                elif msg == "sender: testingMessage":
                    msg_no += 1

            # else:
            #     break
            if msg_no == MESSAGE_BATCH:
                print("Reached 10000! Going to send ack back!")
                grp_send(g_id, "catch'em all")
                msg_no = 0
                break
################################################################################

g_id = join("testingGroup", sys.argv[1])
if g_id == -1:
    print("Error joining the groups!")
    exit()

input("Press enter to start communication: ")

receiveThread = Receiver()
receiveThread.daemon = True
receiveThread.start()

try:
    if sys.argv[1] == "sender":
        print("Sender: ", g_id)
        start_time = time.time()
        for i in range(MESSAGE_BATCH+1):
            grp_send(g_id, "testingMessage")
    # gia olous
    while 1:
        time.sleep(1)
except :
    print("!")

print("Going to leave")
leave(g_id)
