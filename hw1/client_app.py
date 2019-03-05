from client_library import *

SERVICEID = 1

################################ APP FUNCTION ##################################
def main():
    # global end_lifetime
    global sock

    block = 0
    req2wait4 = {}

    while 1:
        try:
            int2check = input("int2check: ")
        except KeyboardInterrupt:
            sock.close()
            print("Ending communication...")
            exit()
        except EOFError:
            while 1:
                if not req2wait4:
                    break
                for req in list(req2wait4.keys()):
                    (getReplyError, answer) = getReply(req, block)
                    if getReplyError == 0:
                        print(" @@@@@@@@@@@@@@ APPLICATION:  ", req2wait4[req], ": ", answer)
                        del req2wait4[req]
                    elif getReplyError == 2:
                        print(req2wait4[req], " has expired. Going to remove it from list")
                        del req2wait4[req]
                    # else:
                    #     print(" ")

            sock.close()
            print("Ending communication...")
            break
        if not int2check:
            sock.close()
            print("Ending communication...")
            exit()

        requestID = sendRequest(SERVICEID, int2check)
        req2wait4[requestID] = int2check

        # while req2wait4:
        for req in list(req2wait4.keys()):
            (getReplyError, answer) = getReply(req, block)
            if getReplyError == 0:
                print(" @@@@@@@@@@@@@@ APPLICATION:  ", req2wait4[req], ": ", answer)
                del req2wait4[req]
            elif getReplyError == 2:
                print(req2wait4[req], " has expired. Going to remove it from list")
                del req2wait4[req]
        time.sleep(1)



if __name__ == "__main__":
    main()
