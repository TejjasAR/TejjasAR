#!/usr/bin/env python3
"""TEJJAS-OS remote terminal.

Visitors run commands on the profile by opening an issue titled `cmd: <command>`.
This script (run by .github/workflows/remote-terminal.yml) parses the issue,
executes the command from a strict allowlist, appends to terminal-log.json,
and rewrites the transcript section of README.md between the
<!-- TERMINAL_LOG_START --> / <!-- TERMINAL_LOG_END --> markers.

Nothing here executes shell input. Commands are allowlisted; all input is
sanitized. No trading content anywhere.
"""
import json
import os
import random
import re
import sys
from datetime import datetime, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(REPO_DIR, "terminal-log.json")
README_PATH = os.path.join(REPO_DIR, "README.md")
MAX_ENTRIES = 6
START = "<!-- TERMINAL_LOG_START -->"
END = "<!-- TERMINAL_LOG_END -->"

FORTUNES = [
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Programs must be written for people to read, and only incidentally for machines to execute.", "Harold Abelson"),
    ("The best error message is the one that never shows up.", "Thomas Fuchs"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Fix the cause, not the symptom.", "Steve Maguire"),
    ("Deleted code is debugged code.", "Jeff Sickel"),
    ("It's not a bug — it's an undocumented feature.", "Anonymous"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
]


def cmd_help(user):
    return "available commands: help · whoami · neofetch · fortune · hack · sudo · matrix · top"


def cmd_whoami(user):
    return f"{user} — clearance level: curious · session logged"


def cmd_neofetch(user):
    return "\n".join([
        "tejjasar@github",
        "───────────────",
        "Host: github.com/TejjasAR",
        "Builds: 8 public repos",
        "Stars: 0 — for now",
        "Top langs: Python · C++ · Java · JS",
        "Uptime: since Oct 2023",
        "Status: building & breaking things",
    ])


def cmd_fortune(user):
    seed = int(os.environ.get("ISSUE_NUMBER", "0") or 0)
    quote, author = random.Random(seed).choice(FORTUNES)
    return f'"{quote}" — {author}'


def cmd_hack(user):
    return "\n".join([
        "initiating breach protocol...",
        "[██████████] 100%",
        "bypassing firewall... done",
        "cracking mainframe... done",
        f"access granted. just kidding, {user} — nice try.",
    ])


def cmd_sudo(user):
    return "guest is not in the sudoers file. This incident will be reported to tejjasar."


def cmd_matrix(user):
    return "\n".join([
        f"Wake up, {user}...",
        "The Matrix has you.",
        "Follow the white rabbit.",
    ])


def cmd_top(user):
    return "\n".join([
        "PID    PROCESS                  FOCUS",
        "1337   cpp-http-server          87%",
        "2048   python-packet-sniffer    72%",
        "4096   ml                       66%",
        "5120   Sentiment_analysis       58%",
    ])


COMMANDS = {
    "help": cmd_help,
    "whoami": cmd_whoami,
    "neofetch": cmd_neofetch,
    "fortune": cmd_fortune,
    "hack": cmd_hack,
    "sudo": cmd_sudo,
    "matrix": cmd_matrix,
    "top": cmd_top,
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


def render_transcript(entries):
    blocks = []
    for e in entries:
        blocks.append(f"{e['user']}@tejjas-os:~$ {e['cmd']}\n{e['out']}")
    return "\n\n".join(blocks)


def update_readme(transcript):
    with open(README_PATH) as f:
        readme = f.read()
    if START not in readme or END not in readme:
        print("markers missing in README; skipping", file=sys.stderr)
        return False
    section = f"{START}\n```text\n{transcript}\n```\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    readme = pattern.sub(section, readme, count=1)
    with open(README_PATH, "w") as f:
        f.write(readme)
    return True


def main():
    out_path = os.environ.get("GITHUB_OUTPUT")
    title = os.environ.get("ISSUE_TITLE", "")
    user = sanitize_user(os.environ.get("ISSUE_USER", ""))
    m = re.match(r"^\s*cmd\s*:\s*(.+?)\s*$", title, re.I | re.S)
    if not m:
        print("not a cmd issue; skipping")
        if out_path:
            with open(out_path, "a") as f:
                f.write("ran=false\n")
        return
    raw = m.group(1).split("\n")[0][:24]
    cmd = re.sub(r"[^a-z0-9_\-]", "", raw.lower()).strip()
    if cmd in COMMANDS:
        output = COMMANDS[cmd](user)
    elif cmd:
        output = f"command not found: {cmd} — try 'help'"
    else:
        output = "empty command — try 'help'"

    entries = load_log()
    entries.append({
        "user": user,
        "cmd": cmd or "(empty)",
        "out": output,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    entries = entries[-MAX_ENTRIES:]
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)

    if update_readme(render_transcript(entries)):
        print(f"executed '{cmd}' for {user}")
    if out_path:
        with open(out_path, "a") as f:
            f.write("ran=true\n")


if __name__ == "__main__":
    main()
