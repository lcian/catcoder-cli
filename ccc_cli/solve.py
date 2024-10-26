#!/usr/bin/env python3
import os
import sys
from typing import Callable

# ===========================================================================================================
# Solve
# ==========================================================================================================


def solve_tc(input: Callable[[], str]) -> str:
    res = ""
    return res


def solve(input: Callable[[], str]) -> str:
    n = int(input())
    res = ""
    for _ in range(n):
        res += solve_tc(input) + "\n"
    return res


# ===========================================================================================================
# Main
# ===========================================================================================================

if __name__ == "__main__":
    run = False
    test = False

    if len(sys.argv) < 2:
        run = True
        test = True
    elif sys.argv[1] == "run":
        run = True
    elif sys.argv[1] == "test":
        test = True

    if test:
        print("Running on example input")
        OKGREEN = "\033[92m"
        FAIL = "\033[91m"
        ENDC = "\033[0m"
        for file in os.listdir("in"):
            if file.endswith(".in") and "example" in file:
                with open(f"in/{file}", "r") as f:
                    res = str(solve(f.readline))
                with open(f"in/{file[:-3]}.out", "r") as f:
                    expected = f.read()
                if res.strip() == expected.strip():
                    print(OKGREEN + "✅" + f"{file} accepted" + ENDC)
                else:
                    print(FAIL + "❌" + f"{file} failed" + ENDC)
                    print()
                    print(f"Got:\n{res}")
                    print()
                    print(f"Expected:\n{expected}")
                    sys.exit(1)
    if test and run:
        print()
    if run:
        print("Running on regular inputs")
        for file in sorted(os.listdir("in")):
            if file.endswith(".in"):
                with open(f"in/{file}", "r") as f:
                    res = str(solve(f.readline))
                    print(f"{file} done")
                with open(f"out/{file[:-3]}.out", "w") as f:
                    f.write(res)
