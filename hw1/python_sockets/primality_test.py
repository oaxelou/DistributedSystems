import sys

def isprime(x):
    for i in range(2, x-1):
        if x % i == 0:
            return False
    else:
        return True
        
x = int(input("Enter number: "))
print x + " is a prime number? " + isprime(x)
