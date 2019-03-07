from slave_server_library import *

SERVICEID = 2

############################### APP  FUNCTION ##################################

def main():
    # global SERVICEID
    register(SERVICEID)
    while 1:
        (client, reqID, message) = getRequest(SERVICEID)
        if((client, reqID, message) == ((0,0), 0, 0)):
            continue
        elif ((client, reqID, message) == ((0,0), 0, 1)):
            print("Another serivce is occuping this machine. I can't operate")
            exit()
        if message == "hello":
            message2send = "hello to you too!"
        else:
            message2send = "Don't know how to answer to that"
        sendReply(client, reqID, message2send)


if __name__ == "__main__":
    main()
