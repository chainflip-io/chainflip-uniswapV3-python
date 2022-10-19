from .utilities import *
from ..src.libraries import SwapMath, SqrtPriceMath

# ComputeSwapStep


def test_exactAmountIn_capped_notOneForZero():
    print("exact amount in that gets capped at price target in one for zero")
    price = encodePriceSqrt(1, 1)
    priceTarget = encodePriceSqrt(101, 100)
    liquidity = expandTo18Decimals(2)
    amount = expandTo18Decimals(1)
    fee = 600
    zeroForOne = False
    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        price, priceTarget, liquidity, amount, fee
    )

    assert int(amountIn) == 9975124224178055
    assert int(feeAmount) == 5988667735148
    assert int(amountOut) == 9925619580021728
    assert (amountIn + feeAmount) < amount, "Entire amount used"

    priceAfterWholeInputAmount = SqrtPriceMath.getNextSqrtPriceFromInput(
        price, liquidity, amount, zeroForOne
    )

    assert int(sqrtQ) == priceTarget, "price not capped at price target"
    assert int(sqrtQ) < int(
        priceAfterWholeInputAmount
    ), "price not less than price after whole input amount"


def test_exactAmountOut_capped_notOneForZero():
    print("exact amount out that gets capped at price target in one for zero")
    price = encodePriceSqrt(1, 1)
    priceTarget = encodePriceSqrt(101, 100)
    liquidity = expandTo18Decimals(2)
    amount = expandTo18Decimals(1) * -1
    fee = 600
    zeroForOne = False

    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        price, priceTarget, liquidity, amount, fee
    )

    assert int(amountIn) == 9975124224178055
    assert int(feeAmount) == 5988667735148
    assert int(amountOut) == 9925619580021728
    assert int(amountOut) < amount * -1, "entire amount out is not returned"

    priceAfterWholeOutputAmount = SqrtPriceMath.getNextSqrtPriceFromOutput(
        price, liquidity, amount * -1, zeroForOne
    )

    assert int(sqrtQ) == priceTarget, "price is capped at price target"
    assert (
        int(sqrtQ) < priceAfterWholeOutputAmount
    ), "price is less than price after whole output amount"


def test_exactAmount_fullySpent_notzeroForOne():
    print("exact amount in that is fully spent in one for zero")
    price = encodePriceSqrt(1, 1)
    priceTarget = encodePriceSqrt(1000, 100)
    liquidity = expandTo18Decimals(2)
    amount = expandTo18Decimals(1)
    fee = 600
    zeroForOne = False

    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        price, priceTarget, liquidity, amount, fee
    )

    assert int(amountIn) == 999400000000000000
    assert int(feeAmount) == 600000000000000
    assert int(amountOut) == 666399946655997866
    assert (int(amountIn) + int(feeAmount)) == amount, "entire amount is used"

    print(type(feeAmount))
    priceAfterWholeInputAmountLessFee = SqrtPriceMath.getNextSqrtPriceFromInput(
        price, liquidity, amount - feeAmount, zeroForOne
    )

    assert int(sqrtQ) < priceTarget, "price does not reach price target"
    assert int(sqrtQ) == int(
        priceAfterWholeInputAmountLessFee
    ), "price is equal to price after whole input amount"


def test_exactAmountOut_fullyReceived_notZeroForOne():
    print("exact amount out that is fully received in one for zero")
    price = encodePriceSqrt(1, 1)
    priceTarget = encodePriceSqrt(1000, 100)
    liquidity = expandTo18Decimals(2)
    amount = expandTo18Decimals(1) * -1
    fee = 600
    zeroForOne = False

    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        price, priceTarget, liquidity, amount, fee
    )

    assert int(amountIn) == 2000000000000000000
    assert int(feeAmount) == 1200720432259356
    assert int(amountOut) == amount * -1

    priceAfterWholeOutputAmount = SqrtPriceMath.getNextSqrtPriceFromOutput(
        price, liquidity, amount * -1, zeroForOne
    )

    assert int(sqrtQ) < priceTarget, "price does not reach price target"
    assert int(sqrtQ) == int(
        priceAfterWholeOutputAmount
    ), "price is equal to price after whole output amount"


def test_exactAmountOut_capped_amountOut():
    print("amount out is capped at the desired amount out")
    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        417332158212080721273783715441582,
        1452870262520218020823638996,
        159344665391607089467575320103,
        -1,
        1,
    )

    assert int(amountIn) == 1
    assert int(feeAmount) == 1
    assert int(amountOut) == 1  ## would be 2 if not capped
    assert int(sqrtQ) == 417332158212080721273783715441581


# This test doesn't make much sence since amountOut is 1 and not 0 since because removed rounding
# However, checking that the other calculations are correct
def test_targetOne_partialInputAmount():
    print("target price of 1 uses partial input amount")
    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        2, 1, 1, 3915081100057732413702495386755767, 1
    )

    assert int(amountIn) == 39614081257132168796771975168
    assert int(feeAmount) == 39614120871253040049813
    assert int(amountIn) + int(feeAmount) <= 3915081100057732413702495386755767
    assert int(amountOut) == 0
    assert int(sqrtQ) == 1


def test_allInput_asFee():
    print("entire input amount taken as fee")
    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        2413, 79887613182836312, 1985041575832132834610021537970, 10, 1872
    )
    assert amountIn == 0
    assert feeAmount == 10
    assert amountOut == 0
    assert sqrtQ == 2413


# This test doesn't make much sence since amountOut is 1 and not 0 since because removed rounding
# However, checking that the other calculations are correct
def test_insuffLiquid_zero_exactOutput():
    print(
        "handles intermediate insufficient liquidity in zero for one exact output case"
    )
    sqrtP = 20282409603651670423947251286016
    sqrtPTarget = sqrtP * 11 // 10
    liquidity = 1024
    ## virtual reserves of one are only 4
    ## https://www.wolframalpha.com/input/?i=1024+%2F+%2820282409603651670423947251286016+%2F+2**96%29
    amountRemaining = -4
    feePips = 3000
    (sqrtQ, amountIn, amountOut, feeAmount) = SwapMath.computeSwapStep(
        sqrtP, sqrtPTarget, liquidity, amountRemaining, feePips
    )

    assert amountOut == 0
    assert sqrtQ == sqrtPTarget
    assert amountIn == 26215
    assert feeAmount == 79
