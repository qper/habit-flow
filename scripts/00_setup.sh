#!/usr/bin/env zsh
# HabitFlow Jira — 00_setup.sh
# Настройка конфигурации: Jira API токен, домен, проект.
# Запуск: ./scripts/00_setup.sh
# Результат: scripts/lib/config.env

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${0}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/lib"

DIVIDER="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "${DIVIDER}"
echo " HabitFlow — Jira Setup"
echo "${DIVIDER}"
echo ""

# ─── Проверки зависимостей ────────────────────────────────────────────────────

check_dep() {
if ! command -v "$1" &>/dev/null; then
echo "❌ Не найден: $1. Установи: $2"
exit 1
fi
echo "✓ $1 найден: $(command -v "$1")"
}

check_dep python3 "brew install python3"
check_dep curl "brew install curl"
check_dep jira "brew install ankitpokhrel/tap/jira-cli"

echo ""
JIRA_VER=$(jira version 2>&1 | head -1 || echo "unknown")
echo "✓ jira-cli: ${JIRA_VER}"
echo ""

# ─── Ввод данных ──────────────────────────────────────────────────────────────

echo "Введи данные Jira Cloud аккаунта:"
echo "(Токен создать: https://id.atlassian.com/manage-profile/security/api-tokens)"
echo ""

read -r "JIRA_EMAIL? Email аккаунта Jira: "
read -rs "JIRA_TOKEN? API Token: "
echo ""

DEFAULT_DOMAIN="habit-flow.atlassian.net"
read -r "JIRA_DOMAIN? Домен Jira [${DEFAULT_DOMAIN}]: "
JIRA_DOMAIN="${JIRA_DOMAIN:-${DEFAULT_DOMAIN}}"

DEFAULT_PROJECT="HF"
read -r "JIRA_PROJECT? Ключ проекта [${DEFAULT_PROJECT}]: "
JIRA_PROJECT="${JIRA_PROJECT:-${DEFAULT_PROJECT}}"

echo ""

# ─── Проверка подключения ─────────────────────────────────────────────────────

echo "Проверяю подключение к ${JIRA_DOMAIN}..."

MYSELF=$(curl -sf \
-H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)" \
-H "Accept: application/json" \
"https://${JIRA_DOMAIN}/rest/api/3/myself" 2>/dev/null || echo "{}")

if ! echo "${MYSELF}" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'accountId' in d else 1)" 2>/dev/null; then
echo ""
echo "❌ Не удалось подключиться к Jira."
echo " Проверь: email, API токен, домен."
echo " Ответ: ${MYSELF}"
exit 1
fi

ACCOUNT_ID=$(echo "${MYSELF}" | python3 -c "import sys,json; print(json.load(sys.stdin)['accountId'])")
DISPLAY_NAME=$(echo "${MYSELF}" | python3 -c "import sys,json; print(json.load(sys.stdin)['displayName'])")

echo "✓ Авторизован как: ${DISPLAY_NAME}"
echo " Account ID: ${ACCOUNT_ID}"
echo ""

# ─── Проверка проекта ────────────────────────────────────────────────────────

echo "Проверяю проект ${JIRA_PROJECT}..."
PROJECT_RESP=$(curl -sf \
-H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)" \
-H "Accept: application/json" \
"https://${JIRA_DOMAIN}/rest/api/3/project/${JIRA_PROJECT}" 2>/dev/null || echo "{}")

if echo "${PROJECT_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'key' in d else 1)" 2>/dev/null; then
PROJECT_NAME=$(echo "${PROJECT_RESP}" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])")
echo "✓ Проект найден: ${PROJECT_NAME} (${JIRA_PROJECT})"
else
echo "⚠️ Проект ${JIRA_PROJECT} не найден или недоступен."
echo " Проверь ключ проекта в Jira."
echo " Продолжаю сохранение конфигурации..."
fi

# ─── Сохранение конфигурации ──────────────────────────────────────────────────

mkdir -p "${LIB_DIR}"
CONFIG_FILE="${LIB_DIR}/config.env"

cat > "${CONFIG_FILE}" <<EOF
# HabitFlow Jira Configuration
# Сгенерировано: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
# ВНИМАНИЕ: не коммить этот файл в git!

export JIRA_DOMAIN="${JIRA_DOMAIN}"
export JIRA_PROJECT="${JIRA_PROJECT}"
export JIRA_EMAIL="${JIRA_EMAIL}"
export JIRA_TOKEN="${JIRA_TOKEN}"
export JIRA_ACCOUNT_ID="${ACCOUNT_ID}"
export JIRA_ME="${JIRA_EMAIL}"
EOF

chmod 600 "${CONFIG_FILE}"
echo ""
echo "✓ Конфигурация сохранена: ${CONFIG_FILE}"

# ─── Создание шаблонов ────────────────────────────────────────────────────────

# epic_keys.env — будет заполнен скриптом 01_create_epics.sh
if [[ ! -f "${LIB_DIR}/epic_keys.env" ]]; then
cat > "${LIB_DIR}/epic_keys.env" <<'TEMPLATE'
# HabitFlow — Epic Keys
# Автоматически заполняется scripts/01_create_epics.sh
# Формат: export EPIC_ENN="PROJECT-KEY"

export EPIC_E01=""
export EPIC_E02=""
export EPIC_E03=""
export EPIC_E04=""
export EPIC_E05=""
export EPIC_E06=""
export EPIC_E07=""
export EPIC_E08=""
export EPIC_E09=""
export EPIC_E10=""
TEMPLATE
echo "✓ Создан шаблон: ${LIB_DIR}/epic_keys.env"
fi

# sprint_ids.env
if [[ ! -f "${LIB_DIR}/sprint_ids.env" ]]; then
cat > "${LIB_DIR}/sprint_ids.env" <<'TEMPLATE'
# HabitFlow — Sprint IDs
# Автоматически заполняется scripts/02_create_sprints.sh

export SPRINT_1=""
export SPRINT_2=""
export SPRINT_3=""
export SPRINT_4=""
export SPRINT_5=""
export SPRINT_6=""
export SPRINT_7=""
TEMPLATE
echo "✓ Создан шаблон: ${LIB_DIR}/sprint_ids.env"
fi

# .gitignore защита
GITIGNORE="${SCRIPT_DIR}/../.gitignore"
if [[ -f "${GITIGNORE}" ]]; then
if ! grep -q "config.env" "${GITIGNORE}" 2>/dev/null; then
echo "scripts/lib/config.env" >> "${GITIGNORE}"
echo "✓ Добавлен config.env в .gitignore"
fi
fi

# ─── Тест Python хелпера ─────────────────────────────────────────────────────

echo ""
echo "Тестирую jira_api.py..."
source "${CONFIG_FILE}"

ME_RESULT=$(python3 "${LIB_DIR}/jira_api.py" me 2>/dev/null || echo "ERROR")
if echo "${ME_RESULT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f' ✓ Python helper работает: {d[\"displayName\"]}')" 2>/dev/null; then
:
else
echo " ⚠️ Python helper: ${ME_RESULT}"
fi

# ─── Итог ─────────────────────────────────────────────────────────────────────

echo ""
echo "${DIVIDER}"
echo "✅ Настройка завершена!"
echo ""
echo "Следующие шаги:"
echo " 1. source scripts/lib/config.env"
echo " 2. ./scripts/01_create_epics.sh"
echo " 3. ./scripts/02_create_sprints.sh"
echo " 4. ./scripts/03_create_dashboard.sh"
echo " 5. Использовать prompts/EPIC_0*.md с LLM для генерации скриптов задач"
echo "${DIVIDER}"