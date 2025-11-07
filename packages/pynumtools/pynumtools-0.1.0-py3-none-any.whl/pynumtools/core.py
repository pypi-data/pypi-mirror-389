"""Core numeric utility functions."""


def round_to(value: float, decimals: int) -> float:
    """Round to specified decimal places."""
    return round(value, decimals)


def to_base(n: int, base: int) -> str:
    """Convert number to different base."""
    if base < 2 or base > 36:
        raise ValueError("Base must be between 2 and 36")
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if n == 0:
        return "0"
    result = ""
    while n > 0:
        result = digits[n % base] + result
        n //= base
    return result


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))
