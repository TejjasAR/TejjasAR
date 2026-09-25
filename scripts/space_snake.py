#!/usr/bin/env python3
"""Recolor Platane/snk contribution-snake SVGs to the deep-space palette.

snk styles everything through CSS variables in a `:root{...}` block, so swapping
the values recolors the grid, the snake, and all animation keyframes at once.
Also adds a comet glow to the serpent.

Usage: python scripts/space_snake.py "dist/*.svg"
"""
import glob
import re
import sys

PALETTE = {
    "--cb": "#030308",  # cell stroke -> black, seamless
    "--cs": "#4ade80",  # the serpent -> classic snake green
    "--ce": "#0b0b16",  # empty cells -> near-black
    "--c0": "#0b0b16",
    "--c1": "#14532d",  # dark green
    "--c2": "#16a34a",  # green
    "--c3": "#4ade80",  # bright green
    "--c4": "#bbf7d0",  # pale green (brightest days)
}

GLOW_RULE = ".s{filter:drop-shadow(0 0 3px #4ade80)}"


def recolor(path):
    svg = open(path).read()

    def sub(m):
        body = m.group(1)
        for var, val in PALETTE.items():
            body = re.sub(re.escape(var) + r":[^;}]+", f"{var}:{val}", body)
        return ":root{" + body + "}"

    new = re.sub(r":root\{([^}]*)\}", sub, svg, count=1)
    if GLOW_RULE not in new:
        new = new.replace("</style>", GLOW_RULE + "</style>", 1)
    open(path, "w").write(new)
    print("recolored", path)


def main():
    paths = [p for pat in sys.argv[1:] for p in glob.glob(pat)]
    if not paths:
        print("no files matched", file=sys.stderr)
        sys.exit(1)
    for path in paths:
        recolor(path)


if __name__ == "__main__":
    main()
