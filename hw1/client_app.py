from client_library import *

# could be moved to _library, but it is only used in _app
import sys

SERVICEID = 1
REQ_TIME_GROUP = 5

################################ APP FUNCTION ##################################
def main():
    # global end_lifetime
    global sock
    if len(sys.argv) > 4 or len(sys.argv) == 1:
        print("Wrong no of args. argv[1]: blocking, argv[2]: testcase, argv[3]: sleep time")
        exit()

    if int(sys.argv[1]) not in [0,1]:
        print("argv[1]: blocking is 0/1")
        exit()

    block = int(sys.argv[1])
    req2wait4 = {}
    sendRequestTime = {}
    delay = {}
    total_delay = {}

    noOfSuccessReq = {}
    interval = -1

    while 1:
        try:
            int2check = input("int2check: ")
            if int2check == "s" and len(sys.argv) == 4:
                time.sleep(int(sys.argv[3]))
                continue
            elif int2check == "s" and len(sys.argv) != 4:
                continue
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
                    if getReplyError == SUCCESS:

                        delay[req] = time.time() - sendRequestTime[req]
                        interval = int(req / REQ_TIME_GROUP)
                        total_delay[interval] += delay[req]
                        noOfSuccessReq[interval] += 1
                        if req % REQ_TIME_GROUP == 0:
                            mean = total_delay[interval] / noOfSuccessReq[interval]
                            print("#sucessful reqs: ", noOfSuccessReq[interval])
                            print( "-> ", time.time(), "\ttotal delay: ", total_delay[interval], "\tmean total delay: ", mean, file=sys.stderr)

                        print("\t\t@@@@@@@@@@@@@@ APPLICATION:  ", req2wait4[req], ": ", answer)
                        del req2wait4[req]
                        del sendRequestTime[req]
                        del delay[req]

                    elif getReplyError == EXPIRED_ERROR:
                        print("\t\t", req2wait4[req], " has expired. Going to remove it from list")
                        del req2wait4[req]
                    elif getReplyError == NO_SERVER_ERROR:
                        print("\t\tNo server available for ", req2wait4[req], ". Going to remove it from list")
                        del req2wait4[req]

            sock.close()
            # print("mean total delay = ", total_delay/noOfSuccessReq)
            print("total delay in each interval:")
            print(total_delay)
            print("mean total delay in each interval:")
            for interval in total_delay:
                try:
                    print(interval, ":", total_delay[interval] / noOfSuccessReq[interval])
                except ZeroDivisionError:
                    print(interval, ": No replies")

            print("Ending communication...")
            break
        if not int2check:
            sock.close()
            print("total delay in each interval:")
            print(total_delay)
            print("mean total delay in each interval:")
            for interval in total_delay:
                try:
                    print(interval, ":", total_delay[interval] / noOfSuccessReq[interval])
                except ZeroDivisionError:
                    print(interval, ": No replies")

            print("Ending communication...")
            # print("mean total delay = ", total_delay/noOfSuccessReq)
            print("Ending communication...")
            exit()

        requestID = sendRequest(SERVICEID, int2check)

        if requestID % REQ_TIME_GROUP == 0:
            interval += 1
            total_delay[interval] = 0
            noOfSuccessReq[interval] = 0


        sendRequestTime[requestID] = time.time()
        # print("\n\n", req2wait4, "\n\n")
        req2wait4[requestID] = int2check
        for req in list(req2wait4.keys()):
            print("req: ", req)
            (getReplyError, answer) = getReply(req, block)

            if getReplyError == SUCCESS:
                delay[req] = time.time() - sendRequestTime[req]
                interval = int(req / REQ_TIME_GROUP)
                total_delay[interval] += delay[req]
                noOfSuccessReq[interval] += 1
                if req % REQ_TIME_GROUP == 0:
                    mean = total_delay[interval] / noOfSuccessReq[interval]
                    print("#sucessful reqs: ", noOfSuccessReq[interval])
                    print( "-> ", time.time(), "\ttotal delay: ", total_delay[interval], "\tmean total delay: ", mean, file=sys.stderr)

                print("\t\t@@@@@@@@@@@@@@ APPLICATION:  ", req2wait4[req], ": ", answer)
                del req2wait4[req]
                del sendRequestTime[req]
                del delay[req]

            elif getReplyError == EXPIRED_ERROR:
                print("\t\t", req2wait4[req], " has expired. Going to remove it from list")
                del req2wait4[req]
            elif getReplyError == NO_SERVER_ERROR:
                print("\t\tNo server available for ", req2wait4[req], ". Going to remove it from list")
                del req2wait4[req]

        # time.sleep(1)



if __name__ == "__main__":
    main()
