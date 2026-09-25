#!/usr/bin/env python3
"""TEJJAS-OS battle log.

Visitors cast spells on the profile by opening an issue titled `cmd: <spell>`.
This script (run by .github/workflows/battle-log.yml) parses the issue,
resolves the spell from a strict allowlist, appends to battle-log.json,
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
W = 800

PROPHECIES = [
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


def spellbook(user, rng):
    return "spellbook: fireball · heal · lightning · prophecy · inspect · steal"


def fireball(user, rng):
    dmg = 100 + rng.randint(0, 60)
    return f"Fireball engulfs the training dummy!\n-{dmg} HP! The dummy collapses. DUMMY DEFEATED."


def heal(user, rng):
    amt = 40 + rng.randint(0, 30)
    return f"Warm light washes over you.\n+{amt} HP! You feel ready for the next quest."


def lightning(user, rng):
    dmg = 70 + rng.randint(0, 50)
    return f"Lightning strikes from a clear sky!\n-{dmg} HP to the training dummy. It smells like ozone."


def prophecy(user, rng):
    quote, author = rng.choice(PROPHECIES)
    return f'The oracle speaks: "{quote}" — {author}'


def inspect(user, rng):
    return f"You inspect the hero.\nLVL 23 Code Warrior. HP 100/100. Status: building & breaking things."


def steal(user, rng):
    return f"You reach for the hero's coin pouch...\nThe hero catches your wrist. 'Nice try.'"


SPELLS = {
    "spellbook": spellbook,
    "fireball": fireball,
    "heal": heal,
    "lightning": lightning,
    "prophecy": prophecy,
    "inspect": inspect,
    "steal": steal,
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
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 340" font-family="Trebuchet MS, Verdana, sans-serif">',
        '<defs><linearGradient id="bgold" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fde68a"/><stop offset="1" stop-color="#f59e0b"/></linearGradient></defs>',
        '<rect x="1" y="1" width="798" height="338" rx="18" fill="#17142f"/>',
        '<text x="40" y="52" font-size="24" font-weight="bold" fill="url(#bgold)" letter-spacing="4">BATTLE LOG</text>',
        '<text x="760" y="48" font-size="13" fill="#a5b4fc" text-anchor="end">visitors cast spells · open an issue titled `cmd: fireball`</text>',
        '<line x1="40" y1="68" x2="760" y2="68" stroke="#fbbf24" stroke-opacity="0.25"/>',
    ]
    y = 102
    for entry in reversed(entries):  # newest first
        user, spell, out = e(entry["user"]), e(entry["cmd"]).upper(), entry["out"]
        parts.append(f'<text x="40" y="{y}" font-size="14" font-weight="bold" fill="#fbbf24">> {user} cast {spell}!</text>')
        y += 22
        for line in wrap(out)[:2]:
            parts.append(f'<text x="58" y="{y}" font-size="12.5" fill="#d1d5db" font-family="Menlo, Consolas, monospace">{e(line)}</text>')
            y += 19
        y += 12
    parts.append('<rect x="1" y="1" width="798" height="338" rx="18" fill="none" stroke="#fbbf24" stroke-opacity="0.35" stroke-width="2"/>')
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
    spell = re.sub(r"[^a-z0-9_\-]", "", raw.lower()).strip()
    if spell in SPELLS:
        output = SPELLS[spell](user, rng)
    elif spell:
        output = f"Unknown spell: '{spell}'. Consult the spellbook."
    else:
        output = "Empty incantation. Consult the spellbook."

    entries = load_log()
    entries.append({"user": user, "cmd": spell or "(empty)", "out": output,
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    entries = entries[-MAX_ENTRIES:]
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    with open(SVG_PATH, "w") as f:
        f.write(render_svg(entries))
    print(f"'{spell}' cast by {user}")
    if out_path:
        with open(out_path, "a") as f:
            f.write("ran=true\n")


if __name__ == "__main__":
    main()
