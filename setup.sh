#!/bin/bash
# =============================================================================
# HabitFlow — Setup: verify jira-cli, configure auth, get accountId
# Run this ONCE before run_all.sh
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/helpers.sh"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   HabitFlow Jira Setup                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# --- 1. Check required tools ---
log_section "Checking required tools"

for tool in jira curl python3 base64; do
    if command -v "$tool" &>/dev/null; then
        log_ok "$tool found: $(command -v $tool)"
    else
        log_error "$tool not found. Install it and re-run setup.sh"
        exit 1
    fi
done

# --- 2. Check jira-cli version ---
JIRA_VER=$(jira version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
log_ok "jira-cli version: $JIRA_VER"

# --- 3. Validate config ---
log_section "Validating config.sh"

if [ "$JIRA_EMAIL" = "your@email.com" ] || [ -z "$JIRA_EMAIL" ]; then
    log_error "Set JIRA_EMAIL in config.sh"
    exit 1
fi
if [ "$JIRA_TOKEN" = "your-api-token" ] || [ -z "$JIRA_TOKEN" ]; then
    log_error "Set JIRA_TOKEN in config.sh (https://id.atlassian.com/manage-profile/security/api-tokens)"
    exit 1
fi
if [ "$PROJECT_KEY" = "HF" ]; then
    log_warn "PROJECT_KEY is 'HF' — confirm this matches your actual Jira project key."
fi
log_ok "Config looks populated"

# --- 4. Write jira-cli config ---
log_section "Writing jira-cli config"

JIRA_CONFIG_DIR="$HOME/.config/jira"
mkdir -p "$JIRA_CONFIG_DIR"

cat > "$JIRA_CONFIG_DIR/.config.yml" << EOF
version: 1
authentication:
  type: bearer
  bearer:
    token: ${JIRA_TOKEN}
server: ${JIRA_URL}
login: ${JIRA_EMAIL}
project:
  key: ${PROJECT_KEY}
  type: scrum
EOF

log_ok "jira-cli config written to $JIRA_CONFIG_DIR/.config.yml"

# --- 5. Test Jira API connectivity ---
log_section "Testing Jira API"

MYSELF_RESP=$(jira_api GET "/rest/api/3/myself" 2>&1)

if echo "$MYSELF_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'accountId' in d else 1)" 2>/dev/null; then
    ACCOUNT_ID=$(echo "$MYSELF_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['accountId'])")
    DISPLAY_NAME=$(echo "$MYSELF_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('displayName','?'))")
    log_ok "Authenticated as: $DISPLAY_NAME ($ACCOUNT_ID)"
else
    log_error "Cannot connect to Jira API. Check JIRA_URL, JIRA_EMAIL, JIRA_TOKEN."
    log_error "Response: $MYSELF_RESP"
    exit 1
fi

# --- 6. Verify project exists ---
log_section "Verifying project: $PROJECT_KEY"

PROJECT_RESP=$(jira_api GET "/rest/api/3/project/${PROJECT_KEY}" 2>&1)
if echo "$PROJECT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'id' in d else 1)" 2>/dev/null; then
    PROJECT_NAME=$(echo "$PROJECT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','?'))")
    PROJECT_ID=$(echo "$PROJECT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','?'))")
    log_ok "Project found: $PROJECT_NAME (id=$PROJECT_ID, key=$PROJECT_KEY)"
else
    log_error "Project '$PROJECT_KEY' not found. Run 'jira project list' to see available projects."
    log_error "Response: $PROJECT_RESP"
    exit 1
fi

# --- 7. Save accountId for use in create scripts ---
log_section "Saving assignee to config"

# Patch config.sh with the real accountId
if grep -q 'JIRA_ASSIGNEE=""' "$SCRIPT_DIR/config.sh"; then
    # On macOS sed needs '' after -i
    sed -i '' "s|^export JIRA_ASSIGNEE=.*|export JIRA_ASSIGNEE=\"${DISPLAY_NAME}\"|" "$SCRIPT_DIR/config.sh"
    log_ok "Set JIRA_ASSIGNEE=\"$DISPLAY_NAME\" in config.sh"
else
    log_info "JIRA_ASSIGNEE already set in config.sh"
fi

# --- 8. Get board ID ---
log_section "Fetching Scrum board ID"

BOARD_RESP=$(jira_agile GET "/rest/agile/1.0/board?projectKeyOrId=${PROJECT_KEY}&type=scrum&maxResults=5")
BOARD_ID=$(echo "$BOARD_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
vals = d.get('values', [])
print(vals[0]['id'] if vals else '')
" 2>/dev/null)

if [ -n "$BOARD_ID" ]; then
    log_ok "Scrum board ID: $BOARD_ID"
    sed -i '' "s|^# export BOARD_ID=.*||g" "$SCRIPT_DIR/config.sh" 2>/dev/null || true
    echo "export BOARD_ID=${BOARD_ID}" >> "$SCRIPT_DIR/config.sh"
    echo "export PROJECT_ID=${PROJECT_ID}" >> "$SCRIPT_DIR/config.sh"
else
    log_warn "No Scrum board found. Sprints won't be created. Create a board manually in Jira first."
fi

# --- 9. Init keys file ---
: > "$KEYS_FILE"
log_ok "Keys file initialised: $KEYS_FILE"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Setup complete! Now run:  ./run_all.sh      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
