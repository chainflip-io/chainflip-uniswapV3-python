import math
from .utilities import *
from ..src.libraries import TickMath


def test_throws_low():
    print("throws for too low test0")
    tryExceptHandler(TickMath.getSqrtRatioAtTick, "T", (MIN_TICK - 1))
    tryExceptHandler(TickMath.getSqrtRatioAtTick, "T", (MAX_TICK + 1))


def test_minTick():
    print("min tick")
    assert TickMath.getSqrtRatioAtTick(MIN_TICK) == 4295128739


def test_minTick_plus_one():
    print("min tick + 1")
    assert TickMath.getSqrtRatioAtTick(MIN_TICK + 1) == 4295343490


def test_maxTick_minus_one():
    print("max tick - 1")
    assert (
        TickMath.getSqrtRatioAtTick(MAX_TICK - 1)
        == 1461373636630004318706518188784493106690254656249
    )


def test_minTickRatio_ltImplementation():
    print("max tick ratio is greater than js implementation")
    assert TickMath.getSqrtRatioAtTick(MIN_TICK) < encodePriceSqrt(1, 2**127)


def test_maxTickRatio_gtImplementation():
    print("max tick ratio is greater than js implementation")
    assert TickMath.getSqrtRatioAtTick(MAX_TICK) > encodePriceSqrt(2**127, 1)


def test_maxTick():
    print("max tick")
    assert (
        TickMath.getSqrtRatioAtTick(MAX_TICK)
        == 1461446703485210103287273052203988822378723970342
    )


def test_ticks():
    absTicks = [
        50,
        100,
        250,
        500,
        1_000,
        2_500,
        3_000,
        4_000,
        5_000,
        50_000,
        150_000,
        250_000,
        500_000,
        738_203,
    ]
    for absTick in absTicks:
        for tick in [-absTick, absTick]:
            print("tick: " + f"{tick}")
            print("is at most off by 1/100th of a bips")
            jsResult = math.sqrt(1.0001 ** (tick)) * 2**96
            result = TickMath.getSqrtRatioAtTick(tick)
            absDiff = abs(result - jsResult)
            assert absDiff / jsResult < 0.01


# MIN_SQRT_RATIO
def test_equals_getSqrtRatioAtTickMinTick():
    print("equals #getSqrtRatioAtTick(MIN_TICK)")
    min = TickMath.getSqrtRatioAtTick(MIN_TICK)
    assert min == TickMath.MIN_SQRT_RATIO


# MAX_SQRT_RATIO
def test_equals_getSqrtRatioAtTickMaxTick():
    print("equals #getSqrtRatioAtTick(MAX_TICK)")
    max = TickMath.getSqrtRatioAtTick(MAX_TICK)
    assert max == TickMath.MAX_SQRT_RATIO


def test_throws_tooLow():
    print("throws for too low ")
    tryExceptHandler(TickMath.getTickAtSqrtRatio, "R", (MIN_SQRT_RATIO - 1))


def test_throws_tooHigh():
    print("throws for too high ")
    tryExceptHandler(TickMath.getTickAtSqrtRatio, "R", MAX_SQRT_RATIO)


def test_ratio_minTick():
    print("ratio if min tick")
    assert TickMath.getTickAtSqrtRatio(MIN_SQRT_RATIO) == MIN_TICK


def test_ratio_minTick_plusOne():
    print("ratio if min tick")
    assert TickMath.getTickAtSqrtRatio(4295343490) == MIN_TICK + 1


def test_ratio_maxTick_minusOne():
    print("ratio if min tick")
    assert (
        TickMath.getTickAtSqrtRatio(1461373636630004318706518188784493106690254656249)
        == MAX_TICK - 1
    )


def test_ratio_closestMaxTick():
    print("ratio closest to max tick")
    assert TickMath.getTickAtSqrtRatio(MAX_SQRT_RATIO - 1) == MAX_TICK - 1


def test_ticks():
    ratios = [
        MIN_SQRT_RATIO,
        encodePriceSqrt(10**12, 1),
        encodePriceSqrt(10**6, 1),
        encodePriceSqrt(1, 64),
        encodePriceSqrt(1, 8),
        encodePriceSqrt(1, 2),
        encodePriceSqrt(1, 1),
        encodePriceSqrt(2, 1),
        encodePriceSqrt(8, 1),
        encodePriceSqrt(64, 1),
        encodePriceSqrt(1, 10**6),
        encodePriceSqrt(1, 10**12),
        MAX_SQRT_RATIO - 1,
    ]

    for ratio in ratios:
        print("ratio: " + f"{ratio}")

        print("is at most off by 1")
        pyResult = math.floor(math.log(((ratio / (2**96)) ** 2), 1.0001))
        result = TickMath.getTickAtSqrtRatio(ratio)
        absDiff = abs(result - pyResult)
        assert absDiff <= 1

        print("ratio is between the tick and tick+1")
        tick = TickMath.getTickAtSqrtRatio(ratio)
        ratioOfTick = TickMath.getSqrtRatioAtTick(tick)
        ratioOfTickPlusOne = TickMath.getSqrtRatioAtTick(tick + 1)
        assert ratio >= ratioOfTick
        assert ratio < ratioOfTickPlusOne
