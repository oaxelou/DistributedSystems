# basic nfs server.
# Just checks the command and:
# 1)  OPEN      a file and stores the fid
# 2)  READ from a file
# 3) WRITE   on a file

import os

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
    print("--------------------")
    print("File " + str(fid) + " has been created")
    print("--------------------")
    return fid

def my_seek(fid, pos, whence):
    try:
        current_pos = os.lseek(fid, pos, whence)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return BadFileDescriptorCode
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
def print_menu():
    menu_str  = "-----------------------\n" + "| Options:\n"
    menu_str += "| -> Open      a file (o)\n" + "| -> Read from a file (r)\n"
    menu_str += "| -> Write  on a file (w)\n"
    menu_str += "| -> Exit (exit)\n"
    menu_str += "-----------------------\n" + "Enter answer: "
    return menu_str
############################################

fid_dictionary = {}
next_fid = 0

def main():
    global fid_dictionary
    global next_fid
    while True:
        option = input(print_menu())
        if   option == 'o':
            fname = input("Enter file name to open: ") # Get name of file
            f = my_open(fname, O_CREAT | O_RDWR) # call my_open
            if f == FileExistsErrorCode:
                print("File already exists...")
                exit()
            elif f == FileNotFoundErrorCode:
                print("File does not exist...")
                exit()
            fid_dictionary[next_fid] = f
            next_fid += 1
        elif option == 'r':
            print(fid_dictionary) # print fids and ask for one
            virtual_fid = int(input("Enter fid: "))
            if virtual_fid not in fid_dictionary:
                print("fid not in database.")
                continue
            fid = fid_dictionary[virtual_fid]
            bytes_to_read = int(input("Enter bytes to read: ")) # ask for bytes
            pos = 0
            bytesRead = my_read(fid, pos, 10)
            if bytesRead == None:
                print("Bad file descriptor (read). Going to terminate...")
                exit()
            print(bytesRead.decode())
        elif option == 'w':
            print(fid_dictionary) # print fids and ask for one
            virtual_fid = int(input("Enter fid: "))
            if virtual_fid not in fid_dictionary:
                print("fid not in database.")
                continue
            fid = fid_dictionary[virtual_fid]
            str_to_write = input("Enter string to write: ") # ask for string
            pos = 0
            bytesWritten = my_write(fid, pos, str_to_write.encode())
            print("bytes written: ", bytesWritten)
            if bytesWritten == BadFileDescriptorCode:
                print("Bad file descriptor (write). Going to terminate...")
                exit()
        elif option == 'exit':
            break
        else:
            print("Going to ignore this answer")

if __name__ == "__main__":
    main()
print("Main is over")
