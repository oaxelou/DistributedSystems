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
        (client, reqID, message) = getRequest(SERVICEID)
        if((client, reqID, message) == ((0,0), 0, 0)):
            continue
        message2send = str(isprime(int(message)))
        sendReply(client, reqID, message2send)


if __name__ == "__main__":
    main()
