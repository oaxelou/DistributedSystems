# basic nfs server.
# Just checks the command and:
# 1)  OPEN      a file and stores the fid
# 2)  READ from a file
# 3) WRITE   on a file

import os

fid_local_dictionary = {}  # virtual_fid: (fid, pos)
next_local_fid = 0
INIT_POS = 0

# na kaneis sunarthsh na dilegei to prwto diathesimo virtual_fid
############################################
O_CREAT = os.O_CREAT
O_EXCL = os.O_EXCL
O_TRUNC = os.O_TRUNC
O_RDWR = os.O_RDWR
O_RDONLY = os.O_RDONLY
O_WRONLY = os.O_WRONLY

SEEK_SET = os.SEEK_SET
SEEK_CUR = os.SEEK_CUR
SEEK_END = os.SEEK_END

FileExistsErrorCode = -1
FileNotFoundErrorCode = -2
BadFileDescriptorCode = -2
############################################
def my_open(fname, mode):
    try:
        fid = os.open(fname, mode)
    except FileExistsError:
        print("File already exists. Going to return FileExistsErrorCode")
        return FileExistsErrorCode
    except FileNotFoundError:
        print("File does not exist. Going to return FileNotFoundErrorCode")
        return FileNotFoundErrorCode
    return fid

def my_seek(fid, pos, whence):
    try:
        current_pos = os.lseek(fid, pos, whence)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        exit()
    return current_pos

def my_read(fid, pos, nofBytes):
    current_pos = my_seek(fid, pos, SEEK_SET)
    print("current position: ", current_pos)
    if current_pos == BadFileDescriptorCode or current_pos == None:
        print("Bad file descriptor (seek). Going to terminate...")
        exit()
    try:
        bytesRead = os.read(fid, nofBytes)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return None
    return bytesRead

def my_write(fid, pos, buf):
    current_pos = my_seek(fid, pos, SEEK_SET)
    print("current position: ", current_pos)
    if current_pos == BadFileDescriptorCode:
        print("Bad file descriptor (seek). Going to terminate...")
        exit()
    try:
        bytesWritten = os.write(fid, buf)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return BadFileDescriptorCode
    return bytesWritten
############################################
############################################
def mynfs_open(fname, mode):
    global fid_local_dictionary
    global INIT_POS
    global next_local_fid
    fid = my_open(fname, mode)                                    # ONLY LOCALLY
    print(fid_local_dictionary)
    fid_local_dictionary[next_local_fid] = (fid, INIT_POS)
    print(fid_local_dictionary)
    next_local_fid += 1
    print("--------------------")
    print("OK: File " + str(next_local_fid-1) + " has been created")
    print("--------------------")
    return next_local_fid-1

def mynfs_close(virtual_fid):
    global fid_local_dictionary
    if virtual_fid not in fid_local_dictionary:
        return FileNotFoundErrorCode
    (fid, _) = fid_local_dictionary[virtual_fid]
    del fid_local_dictionary[virtual_fid]
    os.close(fid)                                                 # ONLY LOCALLY
    print("--------------------")
    print("File " + str(virtual_fid) + " removed")
    print("--------------------")

def mynfs_read(virtual_fid, nofBytes):
    global fid_local_dictionary
    try:
        if virtual_fid not in fid_local_dictionary:
            return FileNotFoundErrorCode
        (fid, pos) = fid_local_dictionary[virtual_fid]
        bytesRead = my_read(fid, pos, nofBytes)                        # ONLY LOCALLY
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return None
    return bytesRead

def mynfs_write(virtual_fid, buf):
    global fid_local_dictionary
    try:
        if virtual_fid not in fid_local_dictionary:
            return FileNotFoundErrorCode
        print("REACHED THIS")
        (fid, pos) = fid_local_dictionary[virtual_fid]
        bytesWritten = my_write(fid, pos, buf)                    # ONLY LOCALLY
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return BadFileDescriptorCode
    return bytesWritten

def mynfs_seek(virtual_fid, pos, whence):
    global fid_local_dictionary
    try:
        if virtual_fid not in fid_local_dictionary:
            return FileNotFoundErrorCode
        (fid, old_pos) = fid_local_dictionary[virtual_fid]
        # to set it to the position that the app sees (in case SEEK_CUR is set)
        current_pos = os.lseek(fid, old_pos, SEEK_SET)            # ONLY LOCALLY
        current_pos = os.lseek(fid, pos, whence)                  # ONLY LOCALLY
        fid_local_dictionary[virtual_fid] = (fid, current_pos)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return BadFileDescriptorCode
    return current_pos
############################################
############################################
def print_menu():
    menu_str  = "-----------------------\n" + "| Options:\n"
    menu_str += "| -> Open      a file (o)\n" + "| -> Read from a file (r)\n"
    menu_str += "| -> Write  on a file (w)\n"
    menu_str += "| -> Close     a file (c)\n"
    menu_str += "| -> Print local dict (p)\n"
    menu_str += "| -> Exit (exit)\n"
    menu_str += "-----------------------\n" + "Enter answer: "
    return menu_str
############################################

def main():
    while True:
        option = input(print_menu())
        if   option == 'o':
            fname = input("Enter file name to open: ") # Get name of file
            f = mynfs_open(fname, O_CREAT | O_RDWR) # call my_open
            if f == FileExistsErrorCode:
                print("File already exists...")
                exit()
            elif f == FileNotFoundErrorCode:
                print("File does not exist...")
                exit()
        elif option == 'r':
            fid = int(input("Enter fid: "))
            bytes_to_read = int(input("Enter bytes to read: ")) # ask for bytes
            bytesRead = mynfs_read(fid, bytes_to_read)
            if bytesRead == None:
                print("Bad file descriptor (read). Going to terminate...")
                exit()
            elif bytesRead == FileNotFoundErrorCode:
                print("Bad file descriptor (read). Going to ignore this")
                continue
            print(bytesRead.decode())
        elif option == 'w':
            fid = int(input("Enter fid: "))
            str_to_write = input("Enter string to write: ") # ask for string
            bytesWritten = mynfs_write(fid, str_to_write.encode())
            print("bytes written: ", bytesWritten)
            if bytesWritten == FileNotFoundErrorCode:
                print("Bad file descriptor (write). Going to ignore this")
                continue
        elif option == 'c':
            if mynfs_close(int(input("Enter fid: "))) == FileNotFoundErrorCode:
                print("Bad file descriptor (write). Going to ignore this")
        elif option == 'p':
            print(fid_local_dictionary)
        elif option == 'exit':
            break
        else:
            print("Going to ignore this answer")

if __name__ == "__main__":
    main()
print("Main is over")
