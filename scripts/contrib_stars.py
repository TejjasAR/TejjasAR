#!/usr/bin/env python3
"""Deep-field contribution star chart.

Fetches the user's GitHub contribution calendar (GraphQL) and renders it as a
pure-black starfield: every day is a star, brighter stars = more contributions.
Replaces the generic green contribution snake with something on-theme.

Usage:
    GH_TOKEN=<token> CONTRIB_USER=TejjasAR python scripts/contrib_stars.py dist/contrib-stars.svg
    python scripts/contrib_stars.py --mock dist/contrib-stars.svg   # render test fixture
"""
import html
import json
import os
import random
import sys
import urllib.request

USER = os.environ.get("CONTRIB_USER", "TejjasAR")
TOKEN = os.environ.get("GH_TOKEN", "")

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def fetch_days():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "deep-field-stars"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    cal = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [day for w in weeks for day in w["contributionDays"]]
    return weeks, days, cal["totalContributions"]


def mock_days():
    random.seed(9)
    weeks = []
    for w in range(53):
        week = []
        for d_ in range(7):
            c = 0 if random.random() < 0.55 else random.choice([1, 1, 2, 2, 3, 4, 6, 9])
            week.append({"contributionCount": c})
        weeks.append({"contributionDays": week})
    days = [day for w in weeks for day in w["contributionDays"]]
    return weeks, days, sum(x["contributionCount"] for x in days)


def style_for(count):
    if count <= 0:
        return 1.6, "#15151f", 0.85
    if count == 1:
        return 2.1, "#3b4a6b", 0.9
    if count <= 3:
        return 2.7, "#22d3ee", 0.85
    if count <= 6:
        return 3.3, "#7dd3fc", 0.95
    return 4.1, "#fbbf24", 1.0


def render(weeks, days, total):
    e = html.escape
    cell, ncols = 15, len(weeks)
    W = ncols * cell + 48
    H = 7 * cell + 92
    ox, oy = 24, 64
    brightest = sorted(range(len(days)), key=lambda i: days[i]["contributionCount"], reverse=True)
    twinklers = set(i for i in brightest[:14] if days[i]["contributionCount"] >= 4)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Trebuchet MS, Verdana, sans-serif">',
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="#030308"/>',
    ]
    random.seed(4)
    for _ in range(26):  # faint background dust
        parts.append(f'<circle cx="{random.randint(10, W-10)}" cy="{random.randint(10, H-10)}" r="0.9" fill="#ffffff" opacity="0.14"/>')

    parts += [
        f'<text x="24" y="36" font-size="22" font-weight="bold" fill="#fbbf24" letter-spacing="5">DEEP FIELD</text>',
        f'<text x="{W-24}" y="32" font-size="13" fill="#8b93b8" text-anchor="end">{total} contributions in the last year</text>',
        f'<line x1="24" y1="48" x2="{W-24}" y2="48" stroke="#fbbf24" stroke-opacity="0.3"/>',
    ]

    idx = 0
    for col, w in enumerate(weeks):
        for row, day in enumerate(w["contributionDays"]):
            c = day["contributionCount"]
            r, fill, op = style_for(c)
            x, y = ox + col * cell + cell / 2, oy + row * cell + cell / 2
            if idx in twinklers:
                dur = round(random.uniform(1.8, 3.4), 1)
                parts.append(
                    f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" opacity="{op}">'
                    f'<animate attributeName="opacity" values="{op};{round(op*0.35, 2)};{op}" '
                    f'keyTimes="0;0.5;1" dur="{dur}s" begin="{round(-random.uniform(0, dur), 1)}s" repeatCount="indefinite"/></circle>')
            else:
                parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" opacity="{op}"/>')
            idx += 1

    parts.append(f'<text x="24" y="{H-16}" font-size="11" fill="#8b93b8" letter-spacing="1">brighter stars = more commits · the void remembers everything</text>')
    parts.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="none" stroke="#fbbf24" stroke-opacity="0.4" stroke-width="2"/>')
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    mock = "--mock" in sys.argv
    out = next((a for a in sys.argv[1:] if not a.startswith("--")), "dist/contrib-stars.svg")
    if mock:
        weeks, days, total = mock_days()
    else:
        if not TOKEN:
            print("GH_TOKEN is required", file=sys.stderr)
            sys.exit(1)
        weeks, days, total = fetch_days()
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        f.write(render(weeks, days, total))
    print(f"wrote {out} ({len(days)} days, {total} contributions)")


if __name__ == "__main__":
    main()
