# Simple program that tests the library between a local file and a remote file
from nfs_alo_client import *

mynfs_set_cache(50, 30)  #size=50 & validity=60sec

fid_remote = mynfs_open("test1.txt", O_CREAT | O_RDWR)
if fid_remote < 0:
    print("Error opening this file")
    exit()

fid_local = os.open("test2.txt", O_CREAT | O_RDWR)
if fid_local < 0:
    print("Error opening this file")
    exit()
###################################################
bytes_read, bytes_buf = mynfs_read(fid_remote, 5)
if bytes_read < 0:
    print("Error opening this file")
    exit()
else:
    print("REMOTELY: I read ", bytes_read)
    if bytes_read:
        print("And the value is: ", bytes_buf)

bytes_read_local = os.read(fid_local, 5)
bytes_read_local = bytes_read_local.decode()
if len(bytes_read_local) < 0:
    print("Error opening this file")
    exit()
else:
    print("LOCALLY: I read ", len(bytes_read_local))
    if bytes_read_local:
        print("And the value is: ", bytes_read_local)

###################################################


bytes_written_remote = mynfs_write(fid_remote, "TESTING")
if bytes_written_remote < 0:
    print("Error opening this file")
    exit()
print("REMOTELY: I wrote ", bytes_written_remote)

bytes_written_local = os.write(fid_local, "TESTING".encode())
if bytes_written_local < 0:
    print("Error opening this file")
    exit()
print("LOCALLY: I wrote ", bytes_written_local)

###################################################
pos_remote = mynfs_seek(fid_remote, 0, SEEK_SET)
if pos_remote < 0:
    print("Error opening this file")
    exit()
else:
    print("REMOTELY: pos ", pos_remote)

pos_local = os.lseek(fid_local, 0, os.SEEK_SET)
if pos_local < 0:
    print("Error opening this file")
    exit()
print("LOCALLY: pos ", pos_local)

###################################################
bytes_read, bytes_buf = mynfs_read(fid_remote, 5)
if bytes_read < 0:
    print("Error opening this file")
    exit()
else:
    print("REMOTELY: I read ", bytes_read)
    if bytes_read:
        print("And the value is: ", bytes_buf)

bytes_read_local = os.read(fid_local, 5)
bytes_read_local = bytes_read_local.decode()
if len(bytes_read_local) < 0:
    print("Error opening this file")
    exit()
print("LOCALLY: I read ", len(bytes_read_local))
if bytes_read_local:
    print("And the value is: ", bytes_read_local)

print("Difference between the two files: ", os.system("diff test1.txt test2.txt"))
