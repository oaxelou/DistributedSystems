# thread and lock cheat sheet


# from threading import Thread, Lock
import threading
from threading import Thread
from threading import Lock
import time
import random

queue = []
lock = Lock()


# allages gia na einai plhrhs o client:
# 1) na mpei auto se mia for kai oci while True wste na elegxoume emeis
# 2) na ginei kai h antitheth pleura pou ousiastika pairnei kai apo allo ena queue

class ProducerThread(Thread):
    def run(self):
        nums = range(5) # this will create the list [0,1,2,3,4]
        global queue
        while True:
            print threading.current_thread(), " Going to produce..."
            num = random.choice(nums) #selects a random number from list
            print threading.current_thread(), "Trying to lock..."
            lock.acquire()
            print threading.current_thread(), " Got the lock! from"
            queue.append(num)
            print "Produced", num
            lock.release()
            time.sleep(random.random())

class ConsumerThread(Thread):
    def run(self):
        global queue
        while True:
            print threading.current_thread(), "Trying to lock..."
            lock.acquire()
            if not queue:
                print "Nothing in queue, but consumer will try to consume"
            else:
                print threading.current_thread(), "Going to pop from queue..."
                num = queue.pop(0)
                print "Consumed", num
            lock.release()
            time.sleep(random.random())

ProducerThread().start()
ConsumerThread().start()
