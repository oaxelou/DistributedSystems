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
            # lock_lifetime.acquire()
            # print(end_lifetime)
            # end_lifetime = 1
            # lock_lifetime.release()
            # print("wait for sender thread")
            # # atMostOnceThread.join()
            # print("wait for receiver thread")
            # sock.close()
            # receiverThread.join()
            print("Ending communication...")
            exit()
        if not int2check:
            sock.close()
            # lock_lifetime.acquire()
            # print(end_lifetime)
            # end_lifetime = 1
            # lock_lifetime.release()
            # print("wait for sender thread")
            # atMostOnceThread.join()
            # print("wait for receiver thread")
            # sock.close()
            #
            # receiverThread.join()
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
            else:
                print(" ")



if __name__ == "__main__":
    main()
