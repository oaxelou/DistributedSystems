from nfs_alo_client import *

def print_flags():
    string = "Flags:"
    string += "\nO_CREAT : " + str(O_CREAT)
    string += "\nO_EXCL  : " + str(O_EXCL)
    string += "\nO_TRUNC : " + str(O_TRUNC)
    string += "\nO_RDWR  : " + str(O_RDWR)
    string += "\nO_RDONLY: " + str(O_RDONLY)
    string += "\nO_WRONLY: " + str(O_WRONLY)
    string += "\nEnter a combination of the above: "
    return string

def print_menu():
    menu_str  = "-----------------------\n" + "| Options:\n"
    menu_str += "| -> Open      a file (o)\n" + "| -> Read from a file (r)\n"
    menu_str += "| -> Write  on a file (w)\n"
    menu_str += "| -> Lseek  on a file (s)\n"
    menu_str += "| -> Close     a file (c)\n"
    menu_str += "| -> Print local dict (p)\n"
    menu_str += "| -> Exit (exit)\n"
    menu_str += "-----------------------\n" + "Enter answer: "
    return menu_str

mynfs_set_cache(50, 30)  #size=50 & validity=60sec

while True:
    option = input(print_menu())
    if option == 'o':
        fname = input("Enter file name to open: ") # Get name of file
        flags = int(input(print_flags()))

        f = mynfs_open(fname, flags) # call my_open
        if f == FileExistsErrorCode:
            print("File already exists...")
        elif f == FileNotFoundErrorCode:
            print("File does not exist...")

    elif option == 'r':
        fid = int(input("Enter fid: "))
        nofBytes = int(input("Enter nofBytes: "))
        bytes_read, bytes_buf = mynfs_read(fid, nofBytes)
        if bytes_read == BadFileDescriptorCode:
            print("Bad File Descriptor")
        else:
            print("I read ", bytes_read)
            if bytes_read:
                print("And the value is: ", bytes_buf)

    elif option == 'w':
        fid = int(input("Enter fid: "))
        bytes_buf = input("Enter bytes to write: ")
        bytes_written = mynfs_write(fid, bytes_buf)
        if bytes_written == BadFileDescriptorCode:
            print("Bad File Descriptor")
        elif bytes_written == PermissionDeniedErrorCode:
            print("Permission Denied to write on this file")
        else:
            print("I wrote", bytes_written, "bytes")

    elif option == 's':
        fid = int(input("Enter fid: "))
        pos = int(input("Enter pos: "))
        whence = int(input("Enter whence([0 set] / [1 cur] / [2 end]) :"))
        current_pos = mynfs_seek(fid, pos, whence)
        if current_pos == WrongWhenceCode:
            print("Error in setting whence")
        else:
            print("Current pos: ", current_pos)

    elif option == 'p':
        print(GREEN, "Cache size:", cache_size, ENDC)
        print(GREEN, fid_local_dictionary, ENDC)

    elif option == 'c':
        fid = int(input("Enter fid: "))
        if mynfs_close(fid) == FileNotFoundErrorCode:
            print("File didn't exist anyway...")
        else:
            print("File closed")

    elif option == 'exit':
        print("Byeeeeee")
        exit()

    elif option == 'bullshit':
        reqID += 1
        request = ("bullshit", 0, reqID)
        send_buf_lock.acquire()
        send_buf[reqID] = request
        send_buf_lock.release()

        recv_buf_lock.acquire()
        while reqID not in recv_buf:
            recv_buf_lock.release()
            time.sleep(0.01)
            recv_buf_lock.acquire()

        print("Received answer for request: ", reqID)  # den to vgazei apo to recv_buf gia na anagnwrizei ta diplotupa!!!!
        print(BLUE, "And the reply is: ", recv_buf[reqID][0], ENDC)
        recv_buf_lock.release()

    else:
        print("ignore")
