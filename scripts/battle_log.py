#!/usr/bin/env python3
"""TEJJAS deep-space comms log.

Visitors transmit signals to the profile by opening an issue titled `cmd: <signal>`.
This script (run by .github/workflows/battle-log.yml) parses the issue,
resolves the signal from a strict allowlist, appends to battle-log.json,
and regenerates assets/battle-log.svg (newest first).

Nothing executes shell input. All input is sanitized. No trading content.
"""
import html
import json
import os
import random
import re
import sys
from datetime import datetime, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(REPO_DIR, "battle-log.json")
SVG_PATH = os.path.join(REPO_DIR, "assets", "battle-log.svg")
MAX_ENTRIES = 5

TRANSMISSIONS = [
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Programs must be written for people to read, and only incidentally for machines to execute.", "Harold Abelson"),
    ("The best error message is the one that never shows up.", "Thomas Fuchs"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Fix the cause, not the symptom.", "Steve Maguire"),
    ("Deleted code is debugged code.", "Jeff Sickel"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
]


def starlog(user, rng):
    return "signals: ping · launch · scan · warp · orbit · distress · signal"


def ping(user, rng):
    return "Ping transmitted into the void...\nPong! Something answered. Probably just a satellite."


def launch(user, rng):
    return "Ignition sequence start.\n3... 2... 1... Liftoff! The probe is away."


def scan(user, rng):
    return "Deep-space scan complete.\nNo alien signals detected. Just the repos, shining."


def warp(user, rng):
    ly = round(rng.uniform(4, 12), 1)
    return f"Warp drive engaged!\n{ly} light-years in 0.3 seconds. Easy."


def orbit(user, rng):
    return "You settle into a stable orbit.\nStatus: calm. View: spectacular."


def distress(user, rng):
    return "Distress beacon activated...\nThe explorer answers: 'I'm fine. Just debugging.'"


def signal(user, rng):
    quote, author = rng.choice(TRANSMISSIONS)
    return f'Incoming transmission from Earth: "{quote}" — {author}'


SIGNALS = {
    "starlog": starlog,
    "ping": ping,
    "launch": launch,
    "scan": scan,
    "warp": warp,
    "orbit": orbit,
    "distress": distress,
    "signal": signal,
}


def sanitize_user(raw):
    return re.sub(r"[^a-zA-Z0-9_\-]", "", raw or "")[:32] or "guest"


def load_log():
    try:
        with open(LOG_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def wrap(text, width=92):
    lines = []
    for para in text.split("\n"):
        while len(para) > width:
            cut = para.rfind(" ", 0, width)
            cut = cut if cut > 0 else width
            lines.append(para[:cut])
            para = para[cut:].lstrip()
        lines.append(para)
    return lines


def render_svg(entries):
    e = html.escape
    n = max(len(entries), 1)
    h = 108 + n * 72 + 34
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {h}" font-family="Trebuchet MS, Verdana, sans-serif">',
        '<defs><linearGradient id="cgold" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fde68a"/><stop offset="1" stop-color="#f59e0b"/></linearGradient></defs>',
        f'<rect x="1" y="1" width="798" height="{h-2}" rx="18" fill="#030308"/>',
    ]
    random.seed(7)
    for _ in range(22):
        x, y = random.randint(10, 790), random.randint(80, h - 10)
        parts.append(f'<circle cx="{x}" cy="{y}" r="1.2" fill="#ffffff" opacity="0.35"/>')
    parts += [
        '<text x="40" y="52" font-size="24" font-weight="bold" fill="url(#cgold)" letter-spacing="5">COMMS LOG</text>',
        '<text x="760" y="48" font-size="13" fill="#8b93b8" text-anchor="end">visitors transmit signals · open an issue titled `cmd: ping`</text>',
        '<line x1="40" y1="68" x2="760" y2="68" stroke="#fbbf24" stroke-opacity="0.3"/>',
    ]
    y = 102
    for entry in reversed(entries):  # newest first
        user, sig, out = e(entry["user"]), e(entry["cmd"]).upper(), entry["out"]
        parts.append(f'<text x="40" y="{y}" font-size="14" font-weight="bold" fill="#fbbf24">&gt; {user} transmitted {sig}</text>')
        y += 22
        for line in wrap(out)[:2]:
            parts.append(f'<text x="58" y="{y}" font-size="12.5" fill="#d1d5db" font-family="Menlo, Consolas, monospace">{e(line)}</text>')
            y += 19
        y += 12
    parts.append(f'<text x="40" y="{y+4}" font-size="13" fill="#8b93b8" font-family="Menlo, Consolas, monospace">&gt; awaiting transmission</text>')
    parts.append(f'<rect x="224" y="{y-9}" width="9" height="17" fill="#22d3ee"><animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    parts.append(f'<rect x="1" y="1" width="798" height="{h-2}" rx="18" fill="none" stroke="#22d3ee" stroke-opacity="0.4" stroke-width="2"/>')
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    out_path = os.environ.get("GITHUB_OUTPUT")
    title = os.environ.get("ISSUE_TITLE", "")
    user = sanitize_user(os.environ.get("ISSUE_USER", ""))
    seed = int(os.environ.get("ISSUE_NUMBER", "0") or 0)
    rng = random.Random(seed)
    m = re.match(r"^\s*cmd\s*:\s*(.+?)\s*$", title, re.I | re.S)
    if not m:
        print("not a cmd issue; skipping")
        if out_path:
            with open(out_path, "a") as f:
                f.write("ran=false\n")
        return
    raw = m.group(1).split("\n")[0][:24]
    sig = re.sub(r"[^a-z0-9_\-]", "", raw.lower()).strip()
    if sig in SIGNALS:
        output = SIGNALS[sig](user, rng)
    elif sig:
        output = f"Unknown signal: '{sig}'. Consult the starlog."
    else:
        output = "Empty transmission. Consult the starlog."

    entries = load_log()
    entries.append({"user": user, "cmd": sig or "(empty)", "out": output,
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    entries = entries[-MAX_ENTRIES:]
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    with open(SVG_PATH, "w") as f:
        f.write(render_svg(entries))
    print(f"'{sig}' transmitted by {user}")
    if out_path:
        with open(out_path, "a") as f:
            f.write("ran=true\n")


if __name__ == "__main__":
    main()
