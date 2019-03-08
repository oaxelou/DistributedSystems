# Distributed Systems - hw1 :
# Asychronous request-reply with at most once and dynamic management of the servers
#                                                        (load balancing)
# Axelou Olympia 2161
# Tsitsopoulou Irene 2203
#
# client_app.py: Client app file
#
#
# arguments:
#   blocking: 0 for non-blocking receiving / 1 for blocking
#   batch size: number of requests to send first, and then wait replies of all of them
#   sleep time: if a line "s" is given as input, the client sleeps for the amount given as
#               argument. If sleep time is given, but "s" is not given as input, sleep time
#               will be ignored

from client_library import *

import sys

SERVICEID = 1
REQ_TIME_GROUP = 5

################################ APP FUNCTION ##################################
def main():
    global sock
    if len(sys.argv) > 4 or len(sys.argv) < 2:
        print("Wrong no of args. argv[1]: blocking (0/1), argv[2]: batch size, argv[3]: sleep time")
        exit()

    if int(sys.argv[1]) not in [0,1]:
        print("argv[1]: blocking is 0/1")
        exit()

    block = int(sys.argv[1])
    batch = int(sys.argv[2])
    sleep_time = int(sys.argv[3])

    req2wait4 = {}
    sendRequestTime = {}
    delay = {}
    total_delay = {}

    noOfSuccessReq = {}
    interval = -1

    if batch != 0:
        while 1:
            for i in range(0, batch):
                try:
                    int2check = input("int2check: ")
                    if int2check == "s" and len(sys.argv) == 4:
                        time.sleep(sleep_time)
                        continue
                except KeyboardInterrupt:
                    sock.close()
                    print("KeyboardInterrupt: Ending communication...")
                    exit()
                # when reading from an input file, client collects replies when reaching EOF
                except EOFError:
                    while 1:
                        if not req2wait4:
                            break
                        # check if any of the requests sent has got a reply from server
                        for req in list(req2wait4.keys()):
                            replies_got = 0
                            (getReplyError, answer) = getReply(req, block)
                            if getReplyError == SUCCESS:
                                # count no of successful replies and calculate delay since sending
                                delay[req] = time.time() - sendRequestTime[req]
                                interval = int(req / REQ_TIME_GROUP)
                                total_delay[interval] += delay[req]
                                noOfSuccessReq[interval] += 1
                                # make groups of #REQ_TIME_GROUP requests to calculate mean delay time
                                if req % REQ_TIME_GROUP == 0:
                                    mean = total_delay[interval] / noOfSuccessReq[interval]
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

                            # break when #batch number of replies have been collected
                            replies_got += 1
                            if replies_got == batch:
                                break

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
                    exit()
                    break
                # close communication when enter is pressed
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
                    exit()

                print(" ")
                requestID = sendRequest(SERVICEID, int2check)
                # make groups of #REQ_TIME_GROUP requests to calculate mean delay time
                if requestID % REQ_TIME_GROUP == 0:
                    interval += 1
                    total_delay[interval] = 0
                    noOfSuccessReq[interval] = 0
                sendRequestTime[requestID] = time.time()
                req2wait4[requestID] = int2check

            # check if any of the requests sent has got a reply from server
            for req in list(req2wait4.keys()):
                (getReplyError, answer) = getReply(req, block)
                if getReplyError == SUCCESS:
                    delay[req] = time.time() - sendRequestTime[req]
                    interval = int(req / REQ_TIME_GROUP)
                    total_delay[interval] += delay[req]
                    noOfSuccessReq[interval] += 1
                    if req % REQ_TIME_GROUP == 0:
                        mean = total_delay[interval] / noOfSuccessReq[interval]
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

################################# DEFAULT ######################################

    else:
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
                exit()

            print("")
            requestID = sendRequest(SERVICEID, int2check)

            if requestID % REQ_TIME_GROUP == 0:
                interval += 1
                total_delay[interval] = 0
                noOfSuccessReq[interval] = 0

            sendRequestTime[requestID] = time.time()
            req2wait4[requestID] = int2check
            for req in list(req2wait4.keys()):
                (getReplyError, answer) = getReply(req, block)

                if getReplyError == SUCCESS:
                    delay[req] = time.time() - sendRequestTime[req]
                    interval = int(req / REQ_TIME_GROUP)
                    total_delay[interval] += delay[req]
                    noOfSuccessReq[interval] += 1
                    if req % REQ_TIME_GROUP == 0:
                        mean = total_delay[interval] / noOfSuccessReq[interval]
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




if __name__ == "__main__":
    main()
