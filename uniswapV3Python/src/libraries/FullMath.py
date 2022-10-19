from .Shared import *

## @notice Calculates ceil(a×b÷denominator) with full precision.
## @param a The multiplicand
## @param b The multiplier
## @param denominator The divisor
## @return result The 256-bit result
def mulDivRoundingUp(a, b, c):
    return divRoundingUp(a * b, c)


## @notice Calculates ceil(a÷denominator) with full precision rounding up.
## @param a The multiplicand
## @param b The divisor
## @return result The 256-bit result
def divRoundingUp(a, b):
    result = a // b
    if a % b > 0:
        result += 1
    return result


## @notice Calculates floor(a×b÷denominator) with full precision. Throws if result overflows a uint256 or denominator == 0
## @param a The multiplicand
## @param b The multiplier
## @param denominator The divisor
## @return result The 256-bit result
def mulDiv(a, b, c):
    result = (a * b) // c
    checkUInt256(result)
    return result
