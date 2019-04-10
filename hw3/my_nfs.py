# Files stuff python

# Source: https://www.tutorialspoint.com/python3/python_files_io.htm

# functions to check out:
# file.flush()
# file.seek(offset, whence)
# whence: 0: start from the begginning of the file
#         1: start from the current position within the file
#         2: start from the end of the file
# file.close()
# file.tell() # tells the current position withing the file
# os.remove(<filename>) # to remove files from the filesystem
# os.rename(old_filename, new_filename)

# The file object attributes:
# file.closed e.g. True/False
# file.mode   e.g. "wb"
# file.name   e.g. "name"

# open stuff:
# open(filename, mode='r', buffering=-1, endocing=None, errors=None, newline=None, clsoefd=True, opener=None)



# Open:
# os.open :
# os.O_CREAT: if the file exists, it has no effect except under O_EXCL below.
# os.O_EXCL: always paired with O_CREAT (if O_CREAT is not set, the result is undefined)
# os.O_TRUNC : if the file exists and it's not opened with O_RDONLY, the size should be truncated to zero and mode and owner should be unchanged.
# os.O_RDWR  : open for both read and write
# os.O_RDONLY: open for reading only
# os.O_WRONLY: open for writing only
############################################
# Seek:
# os.lseek():


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
def mynfs_open(fname, mode):
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
    # print("|", fid)
    # print("|", fid.name)
    # print("|", fid.mode)
    # print("|", fid.closed)
    print("--------------------")
    return fid

def mynfs_close(fid):
    os.close(fid)
    print("--------------------")
    print("File " + str(fid) + " removed")
    # os.remove(fid.name)
    # print("|", fid.name)
    # print("|", fid.mode)
    # print("|", fid.closed)
    print("--------------------")

def mynfs_read(fid, nofBytes):
    try:
        bytesRead = os.read(fid, nofBytes)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return None
    return bytesRead

def mynfs_write(fid, buf):
    try:
        bytesWritten = os.write(fid, buf)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return BadFileDescriptorCode
    return bytesWritten

def mynfs_seek(fid, pos, whence):
    try:
        current_pos = os.lseek(fid, pos, whence)
    except OSError:
        print("Bad file descriptor. Terminating program...")
        return BadFileDescriptorCode
    return current_pos
############################################

# print("os.O_CREAT : ", os.O_CREAT)
# print("os.O_EXCL  : ", os.O_EXCL)
# print("os.O_TRUNC : ", os.O_TRUNC)
# print("os.O_RDWR  : ", os.O_RDWR)
# print("os.O_RDONLY: ", os.O_RDONLY)
# print("os.O_WRONLY: ", os.O_WRONLY)

print("defined...")
print("O_CREAT : ", O_CREAT)
print("O_EXCL  : ", O_EXCL)
print("O_TRUNC : ", O_TRUNC)
print("O_RDWR  : ", O_RDWR)
print("O_RDONLY: ", O_RDONLY)
print("O_WRONLY: ", O_WRONLY)

# print("os.SEEK_SET : ", os.SEEK_SET)
# print("os.SEEK_CUR : ", os.SEEK_CUR)
# print("os.SEEK_END : ", os.SEEK_END)

print("defined...")
print("SEEK_SET : ", SEEK_SET)
print("SEEK_CUR : ", SEEK_CUR)
print("SEEK_END : ", SEEK_END)

############################################
# open
f = mynfs_open(input("Enter file name: "), O_CREAT | O_RDWR)
if f == FileExistsErrorCode:
    print("File already exists...")
    exit()
elif f == FileNotFoundErrorCode:
    print("File does not exist...")
    exit()

# seek
current_pos = mynfs_seek(f, 0, SEEK_SET)
print("current position: ", current_pos)
if current_pos == BadFileDescriptorCode:
    print("Bad file descriptor (seek). Going to terminate...")
    exit()

# read
bytesRead = mynfs_read(f, 10)
if bytesRead == None:
    print("Bad file descriptor (read). Going to terminate...")
    exit()
print(bytesRead.decode())

# seek
current_pos = mynfs_seek(f, 0, SEEK_END)
print("current position: ", current_pos)
if current_pos == BadFileDescriptorCode:
    print("Bad file descriptor (seek). Going to terminate...")
    exit()

# write
bytesWritten = mynfs_write(f, "HELLO\n".encode())
print("bytes written: ", bytesWritten)
if bytesWritten == BadFileDescriptorCode:
    print("Bad file descriptor (write). Going to terminate...")
    exit()

# close
mynfs_close(f)
