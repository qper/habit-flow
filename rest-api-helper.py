#!/usr/bin/env python3
"""
HabitFlow Jira — REST API Helper
Создаёт тикеты, спринты, дашборды через Jira Cloud REST API v3.

Использование:
python3 jira_api.py create --type Task --summary "Title" --description "..." --parent "HF-1"
python3 jira_api.py link --inward HF-10 --outward HF-5 --type "Blocks"
python3 jira_api.py sprint-create --name "Sprint 1" --start 2026-06-29 --end 2026-07-12
python3 jira_api.py sprint-add --sprint-id 42 --issue HF-1
python3 jira_api.py board-id
python3 jira_api.py me
"""

import argparse
import base64
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


# ─── Config from environment ───────────────────────────────────────────────────

def get_env(key: str) -> str:
val = os.environ.get(key, "")
if not val:
print(f"ERROR: env var {key} is not set. Run: source scripts/lib/config.env", file=sys.stderr)
sys.exit(1)
return val


def get_auth_header() -> str:
email = get_env("JIRA_EMAIL")
token = get_env("JIRA_TOKEN")
return "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()


def api_url(path: str) -> str:
domain = get_env("JIRA_DOMAIN")
return f"https://{domain}/{path.lstrip('/')}"


# ─── HTTP helpers ──────────────────────────────────────────────────────────────

def jira_request(method: str, path: str, payload: dict | None = None) -> dict:
url = api_url(path)
data = json.dumps(payload).encode() if payload else None

req = Request(
url,
data=data,
headers={
"Authorization": get_auth_header(),
"Content-Type": "application/json",
"Accept": "application/json",
},
method=method,
)

try:
with urlopen(req, timeout=30) as resp:
body = resp.read()
return json.loads(body) if body else {}
except HTTPError as e:
body = e.read().decode("utf-8", errors="replace")
try:
err = json.loads(body)
except Exception:
err = body
print(f"ERROR {e.code} {method} {url}:\n{json.dumps(err, ensure_ascii=False, indent=2)}", file=sys.stderr)
sys.exit(1)


# ─── ADF builder ───────────────────────────────────────────────────────────────

def text_to_adf(text: str) -> dict:
"""Convert plain-text (with markdown hints) to Atlassian Document Format."""
content = []
lines = text.split("\n")
i = 0

while i < len(lines):
line = lines[i]

# Heading ##
if line.startswith("## "):
content.append({
"type": "heading",
"attrs": {"level": 2},
"content": [{"type": "text", "text": line[3:].strip()}],
})

# Heading ###
elif line.startswith("### "):
content.append({
"type": "heading",
"attrs": {"level": 3},
"content": [{"type": "text", "text": line[4:].strip()}],
})

# Code block ```
elif line.startswith("```"):
code_lines = []
lang = line[3:].strip() or "text"
i += 1
while i < len(lines) and not lines[i].startswith("```"):
code_lines.append(lines[i])
i += 1
content.append({
"type": "codeBlock",
"attrs": {"language": lang},
"content": [{"type": "text", "text": "\n".join(code_lines)}],
})

# Bullet list - [ ] or -
elif line.startswith("- "):
items = []
while i < len(lines) and lines[i].startswith("- "):
item_text = lines[i][2:].strip()
# strip checkbox markers
if item_text.startswith("[ ] ") or item_text.startswith("[x] "):
item_text = item_text[4:]
items.append({
"type": "listItem",
"content": [{
"type": "paragraph",
"content": [{"type": "text", "text": item_text}],
}],
})
i += 1
content.append({"type": "bulletList", "content": items})
continue

# Empty line
elif not line.strip():
content.append({"type": "paragraph", "content": [{"type": "text", "text": " "}]})

# Normal paragraph
else:
content.append({
"type": "paragraph",
"content": [{"type": "text", "text": line}],
})

i += 1

if not content:
content = [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]

return {"type": "doc", "version": 1, "content": content}


# ─── Commands ──────────────────────────────────────────────────────────────────

def cmd_create(args):
"""Create a Jira issue and print its key."""
project = get_env("JIRA_PROJECT")
account_id = get_env("JIRA_ACCOUNT_ID")

fields = {
"project": {"key": project},
"issuetype": {"name": args.type},
"summary": args.summary,
"priority": {"name": args.priority},
"assignee": {"accountId": account_id},
"description": text_to_adf(args.description),
}

if args.parent:
fields["parent"] = {"key": args.parent}

resp = jira_request("POST", "rest/api/3/issue", {"fields": fields})
key = resp.get("key", "")
if not key:
print(f"ERROR: no key in response: {resp}", file=sys.stderr)
sys.exit(1)
print(key)


def cmd_link(args):
"""Link two issues."""
payload = {
"type": {"name": args.type},
"inwardIssue": {"key": args.inward},
"outwardIssue": {"key": args.outward},
}
jira_request("POST", "rest/api/3/issueLink", payload)
print(f"Linked: {args.inward} ← {args.type} → {args.outward}")


def cmd_sprint_create(args):
"""Create a sprint and print its ID."""
board_id = cmd_board_id_raw()
if not board_id:
print("ERROR: board not found", file=sys.stderr)
sys.exit(1)

payload = {
"name": args.name,
"originBoardId": board_id,
"startDate": f"{args.start}T00:00:00.000Z",
"endDate": f"{args.end}T23:59:59.000Z",
"goal": args.goal or "",
}
resp = jira_request("POST", "rest/agile/1.0/sprint", payload)
sprint_id = resp.get("id", "")
if not sprint_id:
print(f"ERROR: {resp}", file=sys.stderr)
sys.exit(1)
print(sprint_id)


def cmd_sprint_add(args):
"""Add an issue to a sprint."""
jira_request(
"POST",
f"rest/agile/1.0/sprint/{args.sprint_id}/issue",
{"issues": [args.issue]},
)
print(f"Added {args.issue} to sprint {args.sprint_id}")


def cmd_board_id_raw() -> int | None:
project = get_env("JIRA_PROJECT")
resp = jira_request("GET", f"rest/agile/1.0/board?projectKeyOrId={project}&type=scrum")
boards = resp.get("values", [])
return boards[0]["id"] if boards else None


def cmd_board_id(args):
bid = cmd_board_id_raw()
print(bid if bid else "")


def cmd_me(args):
resp = jira_request("GET", "rest/api/3/myself")
print(json.dumps({
"accountId": resp.get("accountId"),
"displayName": resp.get("displayName"),
"emailAddress": resp.get("emailAddress"),
}, ensure_ascii=False, indent=2))


def cmd_dashboard_create(args):
project = get_env("JIRA_PROJECT")
payload = {
"name": args.name,
"description": args.description or f"HabitFlow {project} sprint dashboard",
"sharePermissions": [
{"type": "project", "project": {"key": project}}
],
"editPermissions": [],
}
resp = jira_request("POST", "rest/api/3/dashboard", payload)
dashboard_id = resp.get("id", "")
domain = get_env("JIRA_DOMAIN")
print(f"{dashboard_id}")
print(f"URL: https://{domain}/jira/dashboards/{dashboard_id}", file=sys.stderr)


def cmd_update_status(args):
"""Transition issue to a given status name."""
# Get available transitions
resp = jira_request("GET", f"rest/api/3/issue/{args.issue}/transitions")
transitions = resp.get("transitions", [])
target = next((t for t in transitions if t["name"].upper() == args.status.upper()), None)
if not target:
names = [t["name"] for t in transitions]
print(f"ERROR: status '{args.status}' not found. Available: {names}", file=sys.stderr)
sys.exit(1)
jira_request("POST", f"rest/api/3/issue/{args.issue}/transitions",
{"transition": {"id": target["id"]}})
print(f"Transitioned {args.issue} → {args.status}")


# ─── CLI entrypoint ────────────────────────────────────────────────────────────

def main():
parser = argparse.ArgumentParser(description="HabitFlow Jira API Helper")
sub = parser.add_subparsers(dest="command", required=True)

# create
p_create = sub.add_parser("create", help="Create a Jira issue")
p_create.add_argument("--type", required=True, help="Issue type: Epic/Feature/Story/Task/Bug")
p_create.add_argument("--summary", required=True)
p_create.add_argument("--description", default=" ")
p_create.add_argument("--parent", default="")
p_create.add_argument("--priority", default="Medium")
p_create.set_defaults(func=cmd_create)

# link
p_link = sub.add_parser("link", help="Link two issues")
p_link.add_argument("--inward", required=True)
p_link.add_argument("--outward", required=True)
p_link.add_argument("--type", default="Blocks")
p_link.set_defaults(func=cmd_link)

# sprint-create
p_sc = sub.add_parser("sprint-create", help="Create a sprint")
p_sc.add_argument("--name", required=True)
p_sc.add_argument("--start", required=True, help="YYYY-MM-DD")
p_sc.add_argument("--end", required=True, help="YYYY-MM-DD")
p_sc.add_argument("--goal", default="")
p_sc.set_defaults(func=cmd_sprint_create)

# sprint-add
p_sa = sub.add_parser("sprint-add", help="Add issue to sprint")
p_sa.add_argument("--sprint-id", required=True)
p_sa.add_argument("--issue", required=True)
p_sa.set_defaults(func=cmd_sprint_add)

# board-id
p_bid = sub.add_parser("board-id", help="Print Scrum board ID")
p_bid.set_defaults(func=cmd_board_id)

# me
p_me = sub.add_parser("me", help="Print current user info")
p_me.set_defaults(func=cmd_me)

# dashboard-create
p_dash = sub.add_parser("dashboard-create", help="Create a Jira dashboard")
p_dash.add_argument("--name", default="HabitFlow Sprint Dashboard")
p_dash.add_argument("--description", default="")
p_dash.set_defaults(func=cmd_dashboard_create)

# status
p_status = sub.add_parser("status", help="Transition issue to status")
p_status.add_argument("--issue", required=True)
p_status.add_argument("--status", required=True)
p_status.set_defaults(func=cmd_update_status)

args = parser.parse_args()
args.func(args)


if __name__ == "__main__":
main()