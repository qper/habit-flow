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
