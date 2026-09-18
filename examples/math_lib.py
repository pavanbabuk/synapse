def sum_squares(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total

def collatz_steps(n: int) -> int:
    steps = 0
    while n > 1:
        if n % 2 == 0:
            n = n / 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps

def main() -> int:
    sq = sum_squares(100)
    print("Sum of squares (0..99) =", sq)
    steps = collatz_steps(27)
    print("Collatz steps for 27 =", steps)
    return 0
