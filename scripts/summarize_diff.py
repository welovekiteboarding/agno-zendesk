#!/usr/bin/env python3
import os, subprocess, sys, textwrap, json, pathlib, re

API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    sys.exit("❌  ANTHROPIC_API_KEY missing in environment (.env)")

# Get staged diff (cached index, not working tree)
diff = subprocess.check_output(
    ["git", "diff", "--cached", "--unified=0"]
).decode()

# If only CONTEXT_SUMMARY.md is changed, exit cleanly
if re.fullmatch(r"docs/CONTEXT_SUMMARY.md\n", subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"]).decode(), re.M):
    sys.exit(0)

prompt = f"""
Summarise these code changes in 1‑3 concise bullet points (markdown list):
{diff}
"""

import http.client, ssl
conn = http.client.HTTPSConnection("api.anthropic.com", context=ssl.create_default_context())
payload = json.dumps({
  "model": "claude-3-haiku-20240307",
  "max_tokens": 150,
  "temperature": 0.3,
  "messages": [
      {"role": "user", "content": prompt.strip()}
  ]
})
headers = {
  "Content-Type": "application/json",
  "x-api-key": API_KEY,
  "anthropic-version": "2023-06-01"
}
conn.request("POST", "/v1/messages", payload, headers)
resp = json.loads(conn.getresponse().read())
if "content" not in resp or not resp["content"]:
    print("❌ Anthropic API error or invalid response:")
    print(json.dumps(resp, indent=2))
    sys.exit(1)
bullets = resp["content"][0].get("text", "").strip()

summary_file = pathlib.Path("docs/CONTEXT_SUMMARY.md")
summary_file.parent.mkdir(parents=True, exist_ok=True)
if not summary_file.exists():
    summary_file.write_text("# Rolling Context Summary\n\n")
with summary_file.open("a") as f:
    f.write(bullets + "\n")

# Stage the updated file
subprocess.run(["git", "add", "docs/CONTEXT_SUMMARY.md"])
