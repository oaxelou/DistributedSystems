import sys

sendbuff = {}

# add in dictionary
sendbuff.update({1: (41, 0, 0)})
sendbuff[2] = (42, 0, 0)

# key = 3
# sendbuff.update({key: 169})
# key1 = 4
# sendbuff[key1] = 179
#
# sendbuff[3] = 312
# sendbuff[4] = 313
# sendbuff[5] = 314
# sendbuff[6] = 315

# sendbuff.update(3=169)
# sendbuff(dict(4=200))

print(sendbuff)


######################################################
# search in dictionary
item = 1
if item in sendbuff:
    print(str(item) + ": " + str(sendbuff[item]))

# search as tuple AND update value which is a tuple
# (a tuple cannot change so you have to overwrite it)
if (1, (41, 0, 0)) in sendbuff.items():
    print("tuple (41, 0, 0) IS in dictionary")
    (key, (int2send, update_value, random)) = (1, (41, 0, 0))
    sendbuff[key] = (int2send, update_value + 1, random)
else:
    print("tuple (41, 0, 0) ISN'T in dictionary")

print("GOING TO PRINT DICT")
print(sendbuff)

######################################################
# access every item in dictionary
print("Every item in dict + 1")
for item in sendbuff.values():
    (item_value, _, _) = item
    print(str(item_value + 1))

######################################################
# delete from dictionary  (IT EXISTS)

# value_1 = sendbuff.pop(1)
# print("removed 1: " + str(value_1))

value_1 = sendbuff.popitem()
print("removed 1: " + str(value_1))
(key_returned, _) = value_1
print("key from returned thing: " + str(key_returned))
print(sendbuff)


######################################################
# delete from dictionary  (IT DOES NOT EXIST)

try:
    value_NOT = sendbuff.pop(7)
    print("removed 7: " + str(value_NOT))
except KeyError as kerror:
    print("Not found in dictionary")
