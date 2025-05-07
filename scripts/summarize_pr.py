# Trivial change to trigger CI workflow

import openai
import sys
import subprocess
import textwrap
import os

pr = sys.argv[1]
diff = ""
# Try to get PR diff first, fallback to git diff if not a PR
try:
    diff = subprocess.check_output(
        ["gh", "pr", "diff", pr]
    ).decode()
except Exception as e:
    try:
        # Fallback: get last commit diff
        diff = subprocess.check_output(
            ["git", "diff", "HEAD~1", "HEAD"]
        ).decode()
    except Exception as e2:
        print(f"# Both gh pr diff and git diff failed: {e} | {e2}")

prompt = f"Summarise this diff in <=10 bullets:\\n{diff}"
bullets = ""
try:
    bullets = openai.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role":"user","content":prompt}]
    ).choices[0].message.content
except Exception as e:
    print(f"# OpenAI call failed: {e}")

if not bullets or not bullets.strip():
    bullets = "- 📝 Trivial README change merged (auto‑test)."

print("\n" + textwrap.dedent(bullets).strip())
