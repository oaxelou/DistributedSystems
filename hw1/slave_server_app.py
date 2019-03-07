from slave_server_library import *

SERVICEID = 1

############################### APP  FUNCTION ##################################
def isprime(x):
    for i in range(2, x-1):
        if x % i == 0:
            return False
    return True

def main():
    # global SERVICEID
    register(SERVICEID)
    while 1:
        try:
            (client, reqID, message) = getRequest(SERVICEID)
            if (client, reqID, message) == ERROR_INVALID_FORMAT:
                continue
            elif (client, reqID, message) == ERROR_INVALID_SERVICEID:
                print("Another serivce is occuping this machine. I can't operate")
                exit()
            if isinstance(message, int):
                message2send = str(isprime(int(message)))
                sendReply(client, reqID, message2send)
            else:
                message2send = "Not an integer. Don't know what to do with that."
                sendReply(client, reqID, message2send)
        except KeyboardInterrupt:
            print("Keyboard Interrupt detected... Going to unregister slave and quit")
            unregister(SERVICEID)
            break


if __name__ == "__main__":
    main()
