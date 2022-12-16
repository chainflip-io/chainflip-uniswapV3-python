from .utilities import *
from ..src.libraries import TickMath, SqrtPriceMath


def test_fromInput_fails_price_zero():
    print("fails if price is zero")
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromInput,
        "",
        0,
        0,
        expandTo18Decimals(1) // 10,
        False,
    )


def test_fromInput_fails_liquidity_zero():
    print("fails if liquidity is zero")
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromInput,
        "",
        1,
        0,
        expandTo18Decimals(1) // 10,
        True,
    )


def test_fromInput_fails_input_overflow():
    print("fails if input amount overflows the price")
    price = 2**160 - 1
    liquidity = 1024
    amountIn = 1024
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromInput,
        "OF or UF of UINT160",
        price,
        liquidity,
        amountIn,
        False,
    )


def test_fromInput_any_input_overflow():
    print("any input amount cannot underflow the price")
    price = 1
    liquidity = 1
    amountIn = 2**255
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromInput,
        "OF or UF of UINT256",
        price,
        liquidity,
        amountIn,
        False,
    )


def test_fromInput_zeroAmount_zeroForOne():
    print("returns input price if amount in is zero and zeroForOne = true")
    price = 2**96
    assert price == SqrtPriceMath.getNextSqrtPriceFromInput(
        price, expandTo18Decimals(1) // 10, 0, True
    )

    print("returns input price if amount in is zero and zeroForOne = false")
    price = 2**96
    assert price == SqrtPriceMath.getNextSqrtPriceFromInput(
        price, expandTo18Decimals(1) // 10, 0, False
    )


def test_fromInput_zeroAmount_notZeroForOne():
    print("returns the minimum price for max inputs")
    sqrtP = 2**160 - 1
    liquidity = TickMath.MAX_UINT128
    maxAmountNoOverflow = TickMath.MAX_UINT256 - ((liquidity << 96) // sqrtP)
    assert 1 == SqrtPriceMath.getNextSqrtPriceFromInput(
        sqrtP, liquidity, maxAmountNoOverflow, True
    )


def test_fromInput_inputAmount_token1():
    print("input amount of 0.1 token1")
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromInput(
        encodePriceSqrt(1, 1),
        expandTo18Decimals(1),
        int(expandTo18Decimals(1) / 10),
        False,
    )
    assert int(sqrtQ) == 87150978765690771352898345369


def test_fromInput_inputAmount_token0():
    print("input amount of 0.1 token0")
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromInput(
        encodePriceSqrt(1, 1),
        expandTo18Decimals(1),
        int(expandTo18Decimals(1) / 10),
        True,
    )
    assert int(sqrtQ) == 72025602285694852357767227579


def test_fromInput_amountInMaxUint96_zeroForOne():
    print("amountIn > type(uint96).max and zeroForOne = true")

    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromInput(
        encodePriceSqrt(1, 1), expandTo18Decimals(10), 2**100, True
    )
    assert sqrtQ == 624999999995069620


def test_fromInput_amountInMaxUint96_notZeroForOne():
    print("can return 1 with enough amountIn and zeroForOne = true")
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromInput(
        encodePriceSqrt(1, 1), 1, int(TickMath.MAX_UINT256 / 2), True
    )
    assert int(sqrtQ) == 1


# Test getNextSqrtPriceFromOutput
def test_fromOutput_fails_zeroPrice():
    print("fails if price is zero")
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput,
        "",
        0,
        0,
        expandTo18Decimals(1) // 10,
        False,
    )


def test_fromOutput_fails_liquidityZero():
    print("fails if price is zero")
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput,
        "",
        1,
        0,
        expandTo18Decimals(1) // 10,
        True,
    )


def test_fromOutput_fails_equalOutputReserves_token0():
    print("fails if output amount is exactly the virtual reserves of token0")
    price = 20282409603651670423947251286016
    liquidity = 1024
    amountOut = 4
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput, "", price, liquidity, amountOut, False
    )


def test_fromOutput_fails_greaterOutputReserves_token0():
    print("fails if output amount is greater than virtual reserves of token0")
    price = 20282409603651670423947251286016
    liquidity = 1024
    amountOut = 5
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput, "", price, liquidity, amountOut, False
    )


def test_fromOutput_fails_greaterOutputReserves_token1():
    print("fails if output amount is greater than virtual reserves of token1")
    price = 20282409603651670423947251286016
    liquidity = 1024
    amountOut = 262145
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput, "", price, liquidity, amountOut, True
    )


def test_fromOutput_fails_equalOutputReserves_token1():
    print("fails if output amount is exactly the virtual reserves of token1")
    price = 20282409603651670423947251286016
    liquidity = 1024
    amountOut = 262144
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput, "", price, liquidity, amountOut, True
    )


def test_fromOutput_output_lessThanReserves_token1():
    print("succeeds if output amount is just less than the virtual reserves of token1")
    price = 20282409603651670423947251286016
    liquidity = 1024
    amountOut = 262143
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromOutput(price, liquidity, amountOut, True)
    assert int(sqrtQ) == 77371252455336267181195264


def test_fromOutput_puzzlingEchidnaTest():
    print("puzzling echidna test")
    price = 20282409603651670423947251286016
    liquidity = 1024
    amountOut = 4
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput, "", price, liquidity, amountOut, False
    )


def test_fromOutput_zeroAmountIn_zeroForOne():
    print("returns input price if amount in is zero and zeroForOne = true")
    price = encodePriceSqrt(1, 1)
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromOutput(
        price, int(expandTo18Decimals(1) / 10), 0, True
    )
    assert int(sqrtQ) == price


def test_fromOutput_zeroAmountIn_notZeroForOne():
    print("returns input price if amount in is zero and zeroForOne = false")
    price = encodePriceSqrt(1, 1)
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromOutput(
        price, int(expandTo18Decimals(1) / 10), 0, False
    )
    assert int(sqrtQ) == price


def test_fromOutput_outputAmount_token1_notZeroForOne():
    print("output amount of 0.1 token1")
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromOutput(
        encodePriceSqrt(1, 1),
        expandTo18Decimals(1),
        int(expandTo18Decimals(1) / 10),
        False,
    )
    assert int(sqrtQ) == 88031291682515930659493278152


def test_fromOutput_outputAmount_token1_zeroForOne():
    print("output amount of 0.1 token1")
    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromOutput(
        encodePriceSqrt(1, 1),
        expandTo18Decimals(1),
        int(expandTo18Decimals(1) / 10),
        True,
    )
    assert int(sqrtQ) == 71305346262837903834189555302


def test_fails_impossibleAmountOut_zeroForOne():
    print("reverts if amountOut is impossible in zero for one direction")
    # Reverts in divRoundingUp
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput,
        "OF or UF of UINT256",
        encodePriceSqrt(1, 1),
        1,
        int(TickMath.MAX_UINT256 / 2),
        True,
    )


def test_fails_impossibleAmountOut_notZeroForOne():
    print("reverts if amountOut is impossible in zero for one direction")
    tryExceptHandler(
        SqrtPriceMath.getNextSqrtPriceFromOutput,
        "",
        encodePriceSqrt(1, 1),
        1,
        int(TickMath.MAX_UINT256 / 2),
        False,
    )


# getAmount0Delta


def test_getAmount0Delta_zeroLiquidity():
    print("returns if liquidity is zero")
    sqrtQ = SqrtPriceMath.getAmount0Delta(
        encodePriceSqrt(1, 1), encodePriceSqrt(2, 1), 0, True
    )
    assert sqrtQ == 0


def test_getAmount0Delta_equalPrices():
    print("returns 0 if prices are equal")
    sqrtQ = SqrtPriceMath.getAmount0Delta(
        encodePriceSqrt(1, 1), encodePriceSqrt(1, 1), 0, True
    )
    assert sqrtQ == 0


def test_getAmount0Delta_returnsAmount1():
    print("returns 0.1 amount1 for price of 1 to 1.21")

    amount0 = SqrtPriceMath.getAmount0Delta(
        encodePriceSqrt(1, 1), encodePriceSqrt(121, 100), expandTo18Decimals(1), True
    )
    assert int(amount0) == 90909090909090910


def test_getAmount0Delta_priceOverflow():
    print("works for prices that overflow")
    amount0Up = SqrtPriceMath.getAmount0Delta(
        encodePriceSqrt(2**90, 1),
        encodePriceSqrt(2**96, 1),
        expandTo18Decimals(1),
        True,
    )
    amount0Down = SqrtPriceMath.getAmount0Delta(
        encodePriceSqrt(2**90, 1),
        encodePriceSqrt(2**96, 1),
        expandTo18Decimals(1),
        False,
    )

    assert int(amount0Up) == int(amount0Down) + 1


# getAmount1Delta


def test_getAmount1Delta_zeroLiquidity():
    print("returns if liquidity is zero")
    sqrtQ = SqrtPriceMath.getAmount1Delta(
        encodePriceSqrt(1, 1), encodePriceSqrt(2, 1), 0, True
    )
    assert sqrtQ == 0


def test_getAmount1Delta_equalPrices():
    print("returns 0 if prices are equal")
    sqrtQ = SqrtPriceMath.getAmount1Delta(
        encodePriceSqrt(1, 1), encodePriceSqrt(1, 1), 0, True
    )
    assert sqrtQ == 0


def test_getAmount1Delta_returnsAmount1():
    print("returns 0.1 amount1 for price of 1 to 1.21")
    print(encodePriceSqrt(1, 1))
    print(encodePriceSqrt(121, 100))

    amount0 = SqrtPriceMath.getAmount1Delta(
        encodePriceSqrt(1, 1), encodePriceSqrt(121, 100), expandTo18Decimals(1), True
    )
    assert int(amount0) == 100000000000000000

    amount1RoundedDown = SqrtPriceMath.getAmount1Delta(
        encodePriceSqrt(1, 1), encodePriceSqrt(121, 100), expandTo18Decimals(1), False
    )

    assert int(amount1RoundedDown) == int(amount0) - 1


# Swap Computation
def test_swap():
    print("swap computation")
    ## getNextSqrtPriceInvariants(1025574284609383690408304870162715216695788925244,50015962439936049619261659728067971248,406,true)
    sqrtP = 1025574284609383690408304870162715216695788925244
    liquidity = 50015962439936049619261659728067971248
    zeroForOne = True
    amountIn = 406

    sqrtQ = SqrtPriceMath.getNextSqrtPriceFromInput(
        sqrtP, liquidity, amountIn, zeroForOne
    )
    assert int(sqrtQ) == 1025574284609383582644711336373707553698163132913

    amount0Delta = SqrtPriceMath.getAmount0Delta(int(sqrtQ), sqrtP, liquidity, True)
    assert int(amount0Delta) == 406
