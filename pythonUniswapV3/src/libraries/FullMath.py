from .Shared import *

# Using math.ceil or math.floor with simple / doesnt get the exact result.
def mulDivRoundingUp(a, b, c):
    return divRoundingUp(a * b, c)


# From unsafe math ensuring that it outputs the same result as Solidity
def divRoundingUp(a, b):
    result = a // b
    if a % b > 0:
        result += 1
    return result


def mulDiv(a, b, c):
    result = (a * b) // c
    checkUInt256(result)
    return result
