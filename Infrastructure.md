# EPIC 1: Infrastructure & Development Environment
# EPIC 2: Database & Data Layer
# EPIC 3: Authentication & Security
# EPIC 4: Habit Management
# EPIC 5: Tracking Board
# EPIC 6: Statistics & Analytics
# EPIC 7: User Profile & Settings
# EPIC 8: Monitoring & Observability
# EPIC 9: Kubernetes & Helm Deployment
# EPIC 10: CI/CD Pipeline
# EPIC 11: Testing & QA
# EPIC 12: PWA, Mobile UX & Documentation

The user wants me to create a comprehensive ticket hierarchy for the HabitFlow project based on the technical specification document. They want:

Epics → Stories → Tasks hierarchy
Each task should specify which expert performs it
Each task should have detailed assignment and verification criteria
Automated tests/checks where possible
Jira CLI automation scripts for MacOS with zsh
The scripts should create all tickets with "Assignee to me" and Priority==Medium
Sprint creation automation
Dashboard creation
All packaged in a ZIP file for download

Let me first read the skill files that might be relevant, then plan the structure.
Let me think about the ticket hierarchy first based on the ТЗ (Technical Specification):
EPICS:

Infrastructure & DevOps Setup
Authentication & Security
Habit Management (Core)
Daily Tracking & Board
Statistics & Analytics
Frontend UI/UX
Monitoring & Observability
Kubernetes & Helm Deployment
Testing & Quality Assurance
Documentation & Developer Experience

For each Epic, Stories and Tasks:
Let me plan this out comprehensively...
EPIC 1: Infrastructure & DevOps Setup

Story: Repository & Local Dev Environment

Task: Setup monorepo structure with Makefile
Task: Docker Compose for local dev
Task: CI/CD GitHub Actions pipeline


Story: Docker Images

Task: Backend multi-stage Dockerfile
Task: Frontend multi-stage Dockerfile


Story: Database Setup

Task: PostgreSQL configuration
Task: Database migrations setup



EPIC 2: Authentication & Security

Story: User Registration & Login

Task: POST /auth/register endpoint
Task: POST /auth/login endpoint
Task: JWT RS256 implementation


Story: Token Management

Task: Refresh token endpoint
Task: Logout endpoint
Task: Session management


Story: Recovery Codes

Task: Recovery code generation
Task: Recovery code usage endpoint


Story: Security Hardening

…


Отлично, я всё изучил. Буду создавать полную иерархию: 11 эпиков → 33 стори → 106 тасков = 150 тикетов. Начинаю писать скрипты.







# START
mkdir -p /Users/qper/git/github/qper/habit-flow/{epics,sprints,dashboard,keys} && echo "Directories created"







# START
cat > /Users/qper/git/github/qper/habit-flow/config.sh << 'ENDFILE'
#!/bin/bash
# =============================================================================
# HabitFlow — Jira Automation Config
# =============================================================================
# Заполните эти переменные перед запуском run_all.sh

# --- Jira credentials (НЕ коммитьте этот файл в git!) ---
export JIRA_URL="https://habit-flow.atlassian.net"
export JIRA_EMAIL="your@email.com"          # ваш Atlassian email
export JIRA_TOKEN="your-api-token"          # https://id.atlassian.com/manage-profile/security/api-tokens

# --- Проект ---
export PROJECT_KEY="HF"                     # замените на реальный ключ (jira project list)

# --- Assignee ---
# Заполняется автоматически через setup.sh. Если не работает — укажите вручную
export JIRA_ASSIGNEE=""

# --- Настройки ---
export PRIORITY="Medium"
export KEYS_FILE="/tmp/habitflow_jira_keys.env"
export SLEEP_BETWEEN_ISSUES=0.3

# --- Спринты ---
export SPRINT_1_START="2026-06-28T00:00:00.000+0000"
export SPRINT_1_END="2026-07-11T23:59:59.000+0000"
export SPRINT_2_START="2026-07-12T00:00:00.000+0000"
export SPRINT_2_END="2026-08-01T23:59:59.000+0000"
export SPRINT_3_START="2026-08-02T00:00:00.000+0000"
export SPRINT_3_END="2026-08-15T23:59:59.000+0000"
export SPRINT_4_START="2026-08-16T00:00:00.000+0000"
export SPRINT_4_END="2026-08-29T23:59:59.000+0000"
export SPRINT_5_START="2026-08-30T00:00:00.000+0000"
export SPRINT_5_END="2026-09-12T23:59:59.000+0000"
export SPRINT_6_START="2026-09-13T00:00:00.000+0000"
export SPRINT_6_END="2026-09-26T23:59:59.000+0000"
export SPRINT_7_START="2026-09-27T00:00:00.000+0000"
export SPRINT_7_END="2026-10-10T23:59:59.000+0000"
ENDFILE
echo "config.sh written"







# START
cat > /Users/qper/git/github/qper/habit-flow/setup.sh << 'ENDFILE'
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
ENDFILE






# START
chmod +x /Users/qper/git/github/qper/habit-flow/setup.sh
echo "setup.sh written"









# START
cat > /Users/qper/git/github/qper/habit-flow/setup-2.sh << 'ENDFILE'
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
ENDFILE






# START
chmod +x /Users/qper/git/github/qper/habit-flow/setup.sh
echo "setup.sh written"








# START
cat > /Users/qper/git/github/qper/habit-flow/epics/01_auth.sh << 'ENDFILE'
#!/bin/bash
# =============================================================================
# EPIC 1: AUTH — Аутентификация и управление сессиями
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/helpers.sh"
load_keys

log_section "EPIC 1: AUTH — Аутентификация и управление сессиями"

EPIC_DESC=$(cat <<'EOF'
Полный цикл аутентификации: регистрация, JWT RS256 (access 15 мин / refresh 30 дней),
управление сессиями, rate limiting, восстановление через одноразовые recovery codes.
Без внешнего SMTP. Требования: AUTH-01..AUTH-08 из ТЗ раздел 2.1.
EOF
)
EPIC_AUTH=$(create_issue "Epic" "[AUTH] Аутентификация и управление сессиями" "$EPIC_DESC")
save_key "EPIC_AUTH" "$EPIC_AUTH"
[ -z "$EPIC_AUTH" ] && { log_error "Epic AUTH not created, skipping"; return 0 2>/dev/null || exit 0; }

# ─────────────────────────────────────────────────────────────────────────────
# STORY 1.1: Регистрация и управление аккаунтом
# ─────────────────────────────────────────────────────────────────────────────
S_DESC=$(cat <<'EOF'
Как пользователь, я хочу зарегистрироваться по логину и паролю, получить recovery codes
и войти в систему, чтобы начать трекать привычки в приватной self-hosted установке.
Покрывает AUTH-01, AUTH-04 из ТЗ.
EOF
)
STORY_REGISTER=$(create_issue "Story" "[AUTH] Регистрация и управление аккаунтом" "$S_DESC" "$EPIC_AUTH")
save_key "STORY_REGISTER" "$STORY_REGISTER"

# Task 1.1.1
DESC=$(cat <<'EOF'
ЭКСПЕРТ: Backend Developer (Go)

ОПИСАНИЕ: Реализовать HTTP-handler POST /api/v1/auth/register согласно ТЗ AUTH-01.
Endpoint принимает {username, email, password}, создаёт пользователя, хеширует пароль
Argon2id, генерирует 8 recovery codes и возвращает их однократно.

ЗАДАНИЕ:
1. Создать handler Register в internal/api/handler/auth.go
2. Валидация: username 3-50 символов (alphanum+underscore), password ≥8 символов
3. Проверка уникальности username и email (409 Conflict при дубле)
4. Хеширование пароля через alexedwards/argon2id (time=3, mem=65536, threads=2)
5. Генерировать 8 случайных кодов по 10 символов (crypto/rand, base32)
6. Сохранить bcrypt-хеши кодов в таблицу recovery_codes
7. Вернуть 201 с {user_id, username, recovery_codes:[8 codes]}
8. После первого показа коды НЕ возвращать повторно (хранятся только хеши)

КРИТЕРИИ ПРИЁМКИ:
- POST /api/v1/auth/register → 201 с recovery_codes при корректных данных
- 409 если username или email уже занят, поле error.code = "USERNAME_TAKEN" / "EMAIL_TAKEN"
- 400 при невалидных данных с деталями в error.details
- Пароль в БД только как argon2id hash, никогда plaintext
- 8 recovery codes в ответе, каждый 10 символов

ВЕРИФИКАЦИЯ:
curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser","email":"test@test.com","password":"pass1234!"}' | python3 -m json.tool
# Ожидать: {"user_id":"...","username":"testuser","recovery_codes":["...x8..."]}

ТЕСТ: Написать TestRegister в backend/internal/service/auth_test.go
ТЗ REF: раздел 2.1, AUTH-01, AUTH-04
EOF
)
create_issue "Task" "[AUTH] Backend: POST /api/v1/auth/register + validation" "$DESC" "$STORY_REGISTER"

# Task 1.1.2
DESC=$(cat <<'EOF'
ЭКСПЕРТ: Backend Developer (Go) + Security Engineer

ОПИСАНИЕ: Настроить Argon2id хеширование паролей и bcrypt для recovery codes.
Реализовать централизованный password service для предотвращения timing attacks.

ЗАДАНИЕ:
1. Добавить зависимость alexedwards/argon2id в go.mod
2. Создать internal/service/password.go с функциями Hash(password) и Verify(hash, password)
3. Параметры Argon2id: time=3, memory=65536 KiB, threads=2, keyLen=32 — задаются через конфиг
4. Для recovery codes: golang.org/x/crypto/bcrypt, cost=10
5. Все вызовы Verify должны занимать константное время (не прерываться при несовпадении)
6. Написать бенчмарк BenchmarkArgon2Hash в password_test.go (проверить ~100-300ms на hash)

КРИТЕРИИ ПРИЁМКИ:
- Hash(p) и Verify(h,p) работают корректно (unit тест)
- Бенчмарк: хеширование ≥80ms на целевом железе (достаточно медленно для brute-force защиты)
- Параметры вынесены в config, не захардкожены
- Нет plaintext в логах

ВЕРИФИКАЦИЯ:
go test ./internal/service/ -run TestPassword -v
go test ./internal/service/ -bench BenchmarkArgon2Hash -benchtime=5x

ТЗ REF: раздел 3.4, "Все пароли — Argon2id"
EOF
)
create_issue "Task" "[AUTH] Argon2id password hashing + bcrypt recovery codes" "$DESC" "$STORY_REGISTER"

# Task 1.1.3
DESC=$(cat <<'EOF'
ЭКСПЕРТ: Frontend Developer (React/TypeScript)

ОПИСАНИЕ: Создать страницу регистрации /register в React SPA.
Форма: username, email (опционально), password, confirm password.
После успешной регистрации — показать recovery codes в modal с возможностью скопировать.

ЗАДАНИЕ:
1. Создать pages/Auth/RegisterPage.tsx
2. Форма через React Hook Form + Zod схема валидации
3. Поля: username, email, password, confirmPassword
4. Submit → POST /api/v1/auth/register
5. При success: открыть Modal с recovery codes, предупреждение "Сохраните коды!"
6. Кнопка "Скопировать все коды" (Clipboard API)
7. После закрытия modal — редирект на /board (или /login если не залогинен)
8. Обработка ошибок: 409 → "Логин уже занят", 400 → показ field errors

КРИТЕРИИ ПРИЁМКИ:
- Форма валидирует на клиенте (Zod) до отправки
- Recovery codes modal показывает все 8 кодов
- Кнопка "Скопировать" работает (Clipboard API, fallback select+copy)
- Ошибки API отображаются inline у поля

ВЕРИФИКАЦИЯ:
1. Запустить dev server: npm run dev
2. Открыть /register, заполнить форму, нажать Submit
3. Проверить: появился modal с 8 кодами, кнопка Copy работает
4. Попробовать зарегистрировать тот же username → ошибка под полем

ТЗ REF: раздел 8.3 "Экраны"
EOF
)
create_issue "Task" "[AUTH] Frontend: страница регистрации + recovery codes modal" "$DESC" "$STORY_REGISTER"

# Task 1.1.4 — Test
DESC=$(cat <<'EOF'
ЭКСПЕРТ: QA Engineer / Backend Developer

ОПИСАНИЕ: Написать полный набор unit и integration тестов для сервиса регистрации.
Покрытие service layer ≥80%.

ЗАДАНИЕ:
1. Unit тесты в backend/internal/service/auth_test.go:
   - TestRegister_Success: корректная регистрация → user создан, 8 кодов в БД
   - TestRegister_DuplicateUsername: второй вызов с тем же username → error
   - TestRegister_DuplicateEmail: тот же email → error
   - TestRegister_WeakPassword: пароль <8 символов → validation error
   - TestRegister_RecoveryCodesHashed: коды хранятся как bcrypt (не plaintext)
2. Integration тесты в backend/internal/api/handler/auth_test.go (testcontainers):
   - TestRegisterHandler_201: корректный запрос → 201
   - TestRegisterHandler_409: дублирующий username → 409
   - TestRegisterHandler_400: невалидный JSON → 400

КРИТЕРИИ ПРИЁМКИ:
- Все тесты проходят: go test ./... -v
- Coverage service/auth ≥80%: go test ./internal/service/ -cover

ВЕРИФИКАЦИЯ:
go test ./internal/service/ -run TestRegister -v -count=1
go test ./internal/api/handler/ -run TestRegisterHandler -v -count=1 -tags=integration
go test ./internal/service/ -coverprofile=coverage.out && go tool cover -func=coverage.out | grep auth

ТЗ REF: раздел 13.2, TestAuth
EOF
)
create_issue "Task" "[AUTH] Tests: unit+integration тесты регистрации" "$DESC" "$STORY_REGISTER"

# ─────────────────────────────────────────────────────────────────────────────
# STORY 1.2: Вход и управление токенами
# ─────────────────────────────────────────────────────────────────────────────
S_DESC=$(cat <<'EOF'
Как пользователь, я хочу войти в систему и получить JWT access token (15 мин)
и refresh token (30 дней) для автоматического обновления сессии без повторного ввода пароля.
Покрывает AUTH-02, AUTH-07, AUTH-08 из ТЗ.
EOF
)
STORY_LOGIN=$(create_issue "Story" "[AUTH] Вход, JWT токены и rate limiting" "$S_DESC" "$EPIC_AUTH")
save_key "STORY_LOGIN" "$STORY_LOGIN"

# Task 1.2.1
DESC=$(cat <<'EOF'
ЭКСПЕРТ: Backend Developer (Go) + Security Engineer

ОПИСАНИЕ: Реализовать POST /api/v1/auth/login с JWT RS256 и POST /api/v1/auth/refresh
с token rotation. Refresh token хранится в БД (таблица sessions) как bcrypt hash.

ЗАДАНИЕ:
1. Сгенерировать RSA ключевую пару (скрипт scripts/generate-keys.sh)
2. Создать internal/service/token.go:
   - GenerateAccessToken(userID) → JWT RS256, exp=15min
   - GenerateRefreshToken() → UUID, bcrypt hash для хранения
3. POST /auth/login: verify argon2id → issue tokens → вернуть {access_token} + Set-Cookie refresh
4. Refresh cookie: HttpOnly=true, Secure=true, SameSite=Strict
5. POST /auth/refresh: verify refresh hash в sessions → issue new tokens → rotate (старый revoke)
6. POST /auth/logout: revoke refresh token из sessions (revoked_at = NOW())
7. При stolen token (повторное использование отозванного) → немедленно revoke ВСЕ сессии пользователя

КРИТЕРИИ ПРИЁМКИ:
- login → access_token в теле ответа, refresh_token в HttpOnly cookie
- refresh → новый access_token, старый refresh token помечен revoked
- logout → refresh token помечен revoked в sessions
- Повторный use revoked refresh → 401 + все сессии пользователя revoked

ВЕРИФИКАЦИЯ:
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"testuser","password":"pass1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN | python3 -c "
import sys,base64,json
tok=sys.stdin.read().strip()
payload=tok.split('.')[1]+'=='*4
print(json.loads(base64.b64decode(payload[:len(payload)-(len(payload)%4)])))
"

ТЗ REF: раздел 2.1 AUTH-02/03/08, раздел 9.1 Flow, раздел 9.2 Хранение токенов
EOF
)
create_issue "Task" "[AUTH] Backend: POST /auth/login + /auth/refresh + /auth/logout (JWT RS256)" "$DESC" "$STORY_LOGIN"

# Task 1.2.2
DESC=$(cat <<'EOF'
ЭКСПЕРТ: Backend Developer (Go) + Security Engineer

ОПИСАНИЕ: Настроить rate limiting на /auth/* эндпоинтах. 5 неудачных попыток входа
с одного IP → блокировка на 15 минут. Middleware для Echo v4.

ЗАДАНИЕ:
1. Добавить зависимость golang.org/x/time/rate или github.com/ulule/limiter/v3
2. Создать middleware internal/api/middleware/ratelimit.go
3. Rate limit: 5 попыток / 15 минут / IP для /auth/login и /auth/recover
4. Хранить счётчики в памяти (sync.Map) с TTL, при старте очищать
5. При превышении → 429 Too Many Requests с Retry-After заголовком
6. Логировать попытки превышения (zap, уровень warn)
7. Настраиваемые параметры через конфиг (max_attempts, window_duration)

КРИТЕРИИ ПРИЁМКИ:
- 5 успешных запросов → проходят
- 6-й запрос с того же IP в окне → 429 с Retry-After
- После истечения окна → счётчик сбрасывается
- Корректные IPs из X-Forwarded-For при работе за proxy

ВЕРИФИКАЦИЯ:
for i in {1..6}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/api/v1/auth/login \
    -H 'Content-Type: application/json' -d '{"username":"wrong","password":"wrong"}')
  echo "Attempt $i: $STATUS"
done
# Ожидать: 1-5 → 401, 6 → 429

ТЕСТ: TestRateLimit в backend/internal/api/middleware/ratelimit_test.go
ТЗ REF: раздел 2.1 AUTH-07, раздел 9.3 "Brute-force на login: Rate limit 5 попыток / 15 мин / IP"
EOF
)
create_issue "Task" "[AUTH] Rate limiting middleware на /auth/* (5 попыток/15 мин/IP)" "$DESC" "$STORY_LOGIN"

# Task 1.2.3
DESC=$(cat <<'EOF'
ЭКСПЕРТ: Frontend Developer (React/TypeScript)

ОПИСАНИЕ: Страница входа, хранение access token в памяти (не localStorage),
axios/ky interceptor для автоматического обновления через /auth/refresh.

ЗАДАНИЕ:
1. Создать pages/Auth/LoginPage.tsx с формой (React Hook Form + Zod)
2. POST /auth/login → сохранить access_token в Zustand store (memory only, НЕ localStorage)
3. Создать api/client.ts с ky instance:
   - Request hook: добавлять Authorization: Bearer {access_token}
   - Response hook: при 401 → автоматически вызвать /auth/refresh, повторить запрос
   - При ошибке refresh (401) → очистить store → редирект на /login
4. ProtectedRoute компонент: проверять наличие токена, иначе → /login
5. При F5 / перезагрузке: access_token теряется (это нормально), refresh через cookie

КРИТЕРИИ ПРИЁМКИ:
- После логина токен НЕ хранится в localStorage (проверить DevTools → Application → Local Storage)
- При 401 ответе сервера → автоматически /auth/refresh без участия пользователя
- После истечения refresh (или logout на другом устройстве) → редирект на /login
- ProtectedRoute блокирует неавторизованных

ВЕРИФИКАЦИЯ:
1. Войти → в Memory через ky interceptor работает
2. Открыть DevTools, проверить что access_token НЕ в localStorage
3. Подождать 15 мин (или вручную expire token) → следующий API call автоматически refresh

ТЗ REF: раздел 9.2 "Хранение токенов на клиенте"
EOF
)
create_issue "Task" "[AUTH] Frontend: страница логина + token storage in memory + refresh interceptor" "$DESC" "$STORY_LOGIN"

# Task 1.2.4 — Tests
DESC=$(cat <<'EOF'
ЭКСПЕРТ: QA Engineer / Backend Developer

ОПИСАНИЕ: Integration тесты для JWT flow: login, refresh, logout, token theft scenario.
Используются testcontainers-go с реальной PostgreSQL.

ЗАДАНИЕ:
1. Настроить testcontainers-go в backend/internal/testutil/db.go
2. TestLogin_Success: корректные credentials → 200 с access_token в body, Set-Cookie
3. TestLogin_WrongPassword: неверный пароль → 401
4. TestLogin_RateLimit: 6 запросов подряд → 429 на 6-м
5. TestRefresh_Success: валидный refresh cookie → новый access_token
6. TestRefresh_ExpiredToken: истёкший токен → 401
7. TestRefresh_RevokedToken: использованный refresh → 401 + все сессии revoked
8. TestLogout_RevokesToken: logout → refresh token помечен revoked в БД

КРИТЕРИИ ПРИЁМКИ:
- Все тесты проходят: go test ./... -tags=integration -v
- Тесты изолированы (каждый тест начинает с чистой БД)

ВЕРИФИКАЦИЯ:
go test ./internal/api/handler/ -tags=integration -run TestLogin -v
go test ./internal/api/handler/ -tags=integration -run TestRefresh -v
go test ./internal/api/handler/ -tags=integration -run TestLogout -v

ТЗ REF: раздел 13.2 TestAuth
EOF
)
create_issue "Task" "[AUTH] Tests: integration тесты JWT login/refresh/logout flow" "$DESC" "$STORY_LOGIN"

# ─────────────────────────────────────────────────────────────────────────────
# STORY 1.3: Управление сессиями
# ─────────────────────────────────────────────────────────────────────────────
S_DESC=$(cat <<'EOF'
Как пользователь, я хочу видеть все активные сессии и иметь возможность завершить
любую из них или сразу все — например, при подозрении на кражу устройства.
Покрывает AUTH-03 из ТЗ.
EOF
)
STORY_SESSIONS=$(create_issue "Story" "[AUTH] Управление активными сессиями" "$S_DESC" "$EPIC_AUTH")
save_key "STORY_SESSIONS" "$STORY_SESSIONS"

DESC=$(cat <<'EOF'
ЭКСПЕРТ: Backend Developer (Go)

ОПИСАНИЕ: CRUD для управления сессиями: просмотр активных, отзыв одной или всех.
Позволяет завершить сессию на любом устройстве удалённо.

ЗАДАНИЕ:
1. GET /api/v1/auth/sessions: список активных сессий текущего пользователя
   - Поля: id, user_agent, ip_address, created_at, last_used_at
   - Только не-revoked и не-expired
2. DELETE /api/v1/auth/sessions/:id: отзыв конкретной сессии (revoked_at=NOW())
   - Нельзя удалить чужую сессию → 403
3. POST /api/v1/auth/logout-all: revoke ВСЕ сессии пользователя
4. Middleware: обновлять last_used_at при каждом аутентифицированном запросе (async)
5. CronJob или background goroutine: cleanup expired sessions (daily)

КРИТЕРИИ ПРИЁМКИ:
- GET /auth/sessions возвращает только активные сессии текущего пользователя
- DELETE /auth/sessions/:id → 204, refresh cookie этой сессии перестаёт работать
- DELETE чужой сессии → 403 Forbidden
- /auth/logout-all → revoke всех, следующий refresh → 401

ВЕРИФИКАЦИЯ:
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/auth/sessions | python3 -m json.tool
curl -s -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/auth/sessions/SESSION_ID
# Второй вызов с тем же refresh → должен вернуть 401

ТЗ REF: раздел 7.2 "Auth", раздел 9.1
EOF
)
create_issue "Task" "[AUTH] Backend: GET/DELETE /auth/sessions + POST /auth/logout-all" "$DESC" "$STORY_SESSIONS"

DESC=$(cat <<'EOF'
ЭКСПЕРТ: Frontend Developer (React/TypeScript)

ОПИСАНИЕ: UI для страницы управления сессиями в разделе настроек.
Показывает активные сессии с устройством/IP, кнопки завершения.

ЗАДАНИЕ:
1. Создать компонент pages/Settings/SessionsPanel.tsx
2. GET /api/v1/auth/sessions → список карточек сессии
3. Каждая карточка: иконка устройства (UA parsing), IP, дата создания, "сейчас"/"N дней назад"
4. Кнопка "Завершить" у каждой сессии (кроме текущей) → DELETE + убрать из списка
5. Кнопка "Завершить все другие сессии" → /auth/logout-all → redirect /login
6. Текущая сессия помечена "Текущая" и не имеет кнопки удаления

КРИТЕРИИ ПРИЁМКИ:
- Список сессий отображается корректно
- Завершение сессии убирает её из списка без перезагрузки
- Текущая сессия не удаляема из UI
- "Завершить все" → logout

ВЕРИФИКАЦИЯ:
1. Войти с двух браузеров → в обоих видеть две сессии
2. В браузере А завершить сессию Б → в Б следующий запрос → /login

ТЗ REF: раздел 7.2 "Auth", GET /api/v1/auth/sessions
EOF
)
create_issue "Task" "[AUTH] Frontend: UI управления сессиями (Settings)" "$DESC" "$STORY_SESSIONS"

# ─────────────────────────────────────────────────────────────────────────────
# STORY 1.4: Восстановление доступа
# ─────────────────────────────────────────────────────────────────────────────
S_DESC=$(cat <<'EOF'
Как пользователь, я хочу восстановить доступ через одноразовый recovery code,
если забыл пароль, без необходимости SMTP-сервера. Покрывает AUTH-04, AUTH-06.
EOF
)
STORY_RECOVER=$(create_issue "Story" "[AUTH] Восстановление доступа через recovery codes" "$S_DESC" "$EPIC_AUTH")
save_key "STORY_RECOVER" "$STORY_RECOVER"

DESC=$(cat <<'EOF'
ЭКСПЕРТ: Backend Developer (Go)

ОПИСАНИЕ: Реализовать flow восстановления доступа через одноразовый recovery code.
Один код = один вход. После входа — принудительная смена пароля.

ЗАДАНИЕ:
1. POST /api/v1/auth/recover: принимает {username, recovery_code, new_password}
2. Найти неиспользованный код для username: SELECT * FROM recovery_codes WHERE user_id=... AND used_at IS NULL
3. Verify bcrypt(recovery_code, code_hash)
4. Если ок: update recovery_codes SET used_at=NOW() WHERE id=...
5. Обновить пароль пользователя (новый argon2id hash)
6. Revoke все существующие сессии
7. Вернуть новый access_token + set refresh cookie
8. GET /api/v1/me/recovery-codes: количество оставшихся кодов (не сами коды!)
9. POST /api/v1/me/recovery-codes: сгенерировать новые 8 кодов (требует текущий пароль)
10. CLI команда: /server reset-password --username=X --new-password=Y (для администратора на поде)

КРИТЕРИИ ПРИЁМКИ:
- Использованный код → 401 при повторном использовании
- Неиспользованный код → успешный вход + все старые сессии revoked
- GET /me/recovery-codes возвращает только COUNT, не сами коды
- CLI команда работает через kubectl exec

ВЕРИФИКАЦИЯ:
# Тест flow
CODE=$(curl -s http://localhost:8080/api/v1/auth/register -X POST \
  -H 'Content-Type: application/json' -d '{"username":"r","email":"r@r.com","password":"pass1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['recovery_codes'][0])")
curl -s -X POST http://localhost:8080/api/v1/auth/recover \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"r\",\"recovery_code\":\"$CODE\",\"new_password\":\"newpass1234!\"}"
# Повторный вызов с тем же кодом → должен вернуть 401

ТЗ REF: раздел 2.1 AUTH-04/06, "Восстановление доступа"
EOF
)
create_issue "Task" "[AUTH] Backend: POST /auth/recover + recovery codes management + CLI reset" "$DESC" "$STORY_RECOVER"

DESC=$(cat <<'EOF'
ЭКСПЕРТ: Frontend Developer (React/TypeScript)

ОПИСАНИЕ: Страница восстановления доступа /recover для ввода recovery code
и установки нового пароля.

ЗАДАНИЕ:
1. Создать pages/Auth/RecoverPage.tsx
2. Форма: username, recovery_code, new_password, confirm_new_password
3. POST /auth/recover → при успехе редирект на /board (уже залогинен)
4. Ошибки: "Код уже использован", "Код не найден", "Пользователь не найден"
5. Ссылка на /recover на странице /login ("Забыл пароль?")
6. После восстановления показать toast "Пароль изменён. Коды обновите в настройках."

КРИТЕРИИ ПРИЁМКИ:
- Форма работает end-to-end: ввод кода → новый пароль → залогинен
- Неверный код → inline error message
- Использованный код → "Этот код уже использован"

ВЕРИФИКАЦИЯ: E2E тест auth.spec.ts → TestRecover flow (см. задачу E2E тестов)

ТЗ REF: раздел 2.1 AUTH-04, раздел 13.4 "auth.spec.ts"
EOF
)
create_issue "Task" "[AUTH] Frontend: страница восстановления /recover" "$DESC" "$STORY_RECOVER"

log_ok "=== EPIC AUTH завершён: $EPIC_AUTH ==="
ENDFILE






# START
chmod +x /Users/qper/git/github/qper/habit-flow/epics/01_auth.sh
echo "01_auth.sh written"

