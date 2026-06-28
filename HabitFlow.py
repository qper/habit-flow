#!/usr/bin/env python3
"""
HabitFlow — Автоматическое создание иерархии тикетов в Jira
Запускается через run-all.sh или напрямую:
  python3 create_issues.py --project HF --email you@example.com --token TOKEN
"""

import subprocess
import sys
import os
import re
import time
import json
import argparse
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# =============================================================================
# ИЕРАРХИЯ ТИКЕТОВ
# Структура: epics → stories → tasks
# Каждая таска содержит: summary, description (markdown), expert, sprint (1-7)
# =============================================================================

ISSUES = [
    # =========================================================================
    # EPIC 1: Infrastructure & Development Environment
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[INFRA] Infrastructure & Development Environment",
        "description": (
            "Закладывает фундамент всего проекта: структура репозитория, локальное окружение, "
            "CI/CD-скелет, Docker-compose, Makefile и базовые настройки всех сервисов.\n\n"
            "**Фаза:** Phase 0 — Foundations\n"
            "**Цель:** Команда может клонировать репозиторий и запустить всё одной командой `make dev`."
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Repository & Dev Environment Setup",
                "description": "Инициализация монорепозитория со структурой из ТЗ §12, Makefile, docker-compose и CI-заготовками.",
                "sprint": 1,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Инициализация структуры монорепозитория",
                        "description": (
                            "## Описание\n"
                            "Создать структуру директорий монорепозитория строго по ТЗ §12: "
                            "`backend/`, `frontend/`, `helm/`, `docs/`, `scripts/`, `.github/workflows/`. "
                            "Добавить `.gitignore` (Go, Node, secrets, output dirs), `README.md`-заглушку, "
                            "`.editorconfig` (UTF-8, LF, 2-space indent для TS/YAML, 4-space для Go).\n\n"
                            "## Исполнитель\n🎯 Tech Lead\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все директории из ТЗ §12 присутствуют\n"
                            "- [ ] `.gitignore` покрывает: `*.env`, `output/`, `node_modules/`, `dist/`, `vendor/`, secrets\n"
                            "- [ ] `git init && git add . && git commit` проходит без предупреждений\n"
                            "- [ ] README содержит badges: Build Status, License\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "# Запустить из корня репозитория\n"
                            "for dir in backend frontend helm docs scripts .github/workflows; do\n"
                            "  [ -d \"$dir\" ] || echo \"MISSING: $dir\"\n"
                            "done\n"
                            "```"
                        ),
                        "expert": "Tech Lead",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Создать Makefile со всеми целями из ТЗ §12.1",
                        "description": (
                            "## Описание\n"
                            "Создать `Makefile` с целями: `dev`, `test`, `test-e2e`, `lint`, `generate`, "
                            "`build`, `push`, `helm-lint`, `helm-diff`, `deploy`, `port-forward`, `backup-now`, `logs`. "
                            "Каждая цель должна выводить цветное сообщение о начале работы. "
                            "Добавить `.PHONY` для всех целей. Переменные `REGISTRY`, `TAG`, `NAMESPACE` брать из env.\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `make help` выводит список всех целей с описаниями\n"
                            "- [ ] `make lint` запускает golangci-lint + eslint без ошибок на чистом проекте\n"
                            "- [ ] `make build` собирает Docker-образы backend и frontend\n"
                            "- [ ] Все переменные имеют дефолтные значения\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "make help | grep -E 'dev|test|lint|build|deploy'\n"
                            "# Должен напечатать все 12 целей\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Настроить docker-compose.yml для локальной разработки",
                        "description": (
                            "## Описание\n"
                            "Создать `docker-compose.yml` с сервисами: `postgres` (v16-alpine), "
                            "`backend` (hot-reload через Air), `frontend` (Vite dev server). "
                            "Создать `docker-compose.override.yml` с опциональными сервисами: "
                            "`prometheus`, `grafana`, `loki`. "
                            "Healthcheck для postgres. Named volumes для данных. "
                            "`POSTGRES_DB=habitflow`, `POSTGRES_USER=habitflow`. "
                            "Все переменные из `.env.local` (добавить `.env.local.example`).\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `docker-compose up -d` поднимает все сервисы без ошибок\n"
                            "- [ ] backend доступен на `localhost:8080/healthz` → 200\n"
                            "- [ ] frontend доступен на `localhost:3000` → HTML страница\n"
                            "- [ ] postgres healthcheck проходит в течение 30 секунд\n"
                            "- [ ] `docker-compose down -v` очищает всё\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "docker-compose up -d && sleep 15\n"
                            "curl -sf http://localhost:8080/healthz || exit 1\n"
                            "curl -sf http://localhost:3000 || exit 1\n"
                            "echo '✅ docker-compose OK'\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Скелет GitHub Actions CI (ci.yml)",
                        "description": (
                            "## Описание\n"
                            "Создать `.github/workflows/ci.yml` со следующими jobs: "
                            "`backend-lint` (golangci-lint), `backend-test` (go test), "
                            "`frontend-lint` (eslint + tsc), `frontend-test` (vitest), "
                            "`helm-validate` (helm lint + kubeval), `security-scan` (gosec + trivy). "
                            "Использовать matrix strategy для Go версий. "
                            "Кэш Go modules и npm. Artifact upload для test reports.\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] CI запускается на push и pull_request\n"
                            "- [ ] Все jobs параллельны там, где нет зависимостей\n"
                            "- [ ] Кэш работает: повторный запуск на 40%+ быстрее\n"
                            "- [ ] Неудачный тест блокирует merge\n\n"
                            "## Автоматизированная проверка\n"
                            "Push в PR → проверить что все check'и отображаются в GitHub."
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 1,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Backend Go Foundation",
                "description": "Базовая структура Go-приложения: Echo сервер, конфигурация, логгер, healthcheck, Prometheus endpoint.",
                "sprint": 1,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Инициализировать Go-модуль, Echo v4, main.go",
                        "description": (
                            "## Описание\n"
                            "Инициализировать Go-модуль `github.com/smirnofflab/habitflow`. "
                            "Создать `cmd/server/main.go` с Echo v4 сервером. "
                            "Структура пакетов строго по ТЗ §12: `internal/api/`, `internal/domain/`, "
                            "`internal/service/`, `internal/repository/`, `internal/config/`, `internal/metrics/`. "
                            "Graceful shutdown (SIGTERM/SIGINT с таймаутом 30 сек). "
                            "Версия приложения через `ldflags`.\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `go build ./...` проходит без ошибок\n"
                            "- [ ] Сервер стартует и слушает `:8080`\n"
                            "- [ ] Graceful shutdown: CTRL+C завершает все соединения до выхода\n"
                            "- [ ] `go vet ./...` без предупреждений\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "// TestServerStarts in main_test.go\n"
                            "func TestServerStarts(t *testing.T) {\n"
                            "    go main()\n"
                            "    time.Sleep(100 * time.Millisecond)\n"
                            "    resp, err := http.Get(\"http://localhost:8080/healthz\")\n"
                            "    assert.NoError(t, err)\n"
                            "    assert.Equal(t, 200, resp.StatusCode)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Конфигурация через Viper + структурированный логгер Zap",
                        "description": (
                            "## Описание\n"
                            "Подключить `spf13/viper` для загрузки конфигурации из ENV и YAML. "
                            "Конфиг-структура в `internal/config/config.go` должна включать: "
                            "`Server.Port`, `DB.DSN`, `JWT.AccessExpiry`, `JWT.RefreshExpiry`, "
                            "`EditWindowDays`, `LogLevel`, `DBPoolSize`. "
                            "Подключить `uber-go/zap` в JSON-режиме. "
                            "Middleware для Echo: каждый запрос логируется с полями: method, path, status, duration_ms, trace_id.\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `LOG_LEVEL=debug ./server` выводит debug-логи\n"
                            "- [ ] Каждый HTTP-запрос генерирует JSON-запись с обязательными полями\n"
                            "- [ ] Секреты (DB_PASSWORD, JWT ключи) не попадают в логи\n"
                            "- [ ] Конфиг читается из ENV и из `config.yaml` с приоритетом ENV\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "curl -s http://localhost:8080/healthz 2>&1\n"
                            "# В stdout сервера должна появиться JSON-строка с полями:\n"
                            "# method, path, status, duration_ms\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Реализовать GET /healthz и GET /readyz",
                        "description": (
                            "## Описание\n"
                            "Реализовать два эндпоинта для Kubernetes probes:\n"
                            "- `GET /healthz` — liveness probe, возвращает `{\"status\":\"ok\",\"version\":\"1.0.0\"}` всегда\n"
                            "- `GET /readyz` — readiness probe, проверяет соединение с БД (`SELECT 1`), "
                            "возвращает 200 если OK, 503 если БД недоступна с телом `{\"status\":\"db_unavailable\"}`\n"
                            "Эти эндпоинты НЕ требуют аутентификации и НЕ логируются (исключить из access log).\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `GET /healthz` → 200 даже когда БД недоступна\n"
                            "- [ ] `GET /readyz` → 503 при остановленной postgres\n"
                            "- [ ] Оба эндпоинта отвечают < 100ms\n"
                            "- [ ] Не пишутся в access log\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestHealthz(t *testing.T) {\n"
                            "    // healthz всегда 200\n"
                            "    resp := httptest.NewRecorder()\n"
                            "    handler.Healthz(resp, req)\n"
                            "    assert.Equal(t, 200, resp.Code)\n"
                            "}\n"
                            "func TestReadyz_DBDown(t *testing.T) {\n"
                            "    // readyz 503 при недоступной БД\n"
                            "    resp := httptest.NewRecorder()\n"
                            "    handler.Readyz(mockDB)(resp, req)\n"
                            "    assert.Equal(t, 503, resp.Code)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Prometheus /metrics эндпоинт",
                        "description": (
                            "## Описание\n"
                            "Подключить `prometheus/client_golang` и настроить `/metrics` эндпоинт. "
                            "Зарегистрировать базовые метрики из ТЗ §10.1: "
                            "`habitflow_http_requests_total`, `habitflow_http_request_duration_seconds`, "
                            "`habitflow_http_requests_in_flight`. "
                            "Метрики живут на отдельном порту `:9090` (не `:8080`) для изоляции от API.\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `curl http://localhost:9090/metrics` возвращает текст в формате Prometheus\n"
                            "- [ ] После запроса к API в метриках появляется соответствующая запись\n"
                            "- [ ] `/metrics` недоступен через внешний Ingress (только ServiceMonitor)\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "curl -s http://localhost:9090/metrics | grep habitflow_http_requests_total\n"
                            "# Должно вернуть как минимум одну строку\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Frontend React Foundation",
                "description": "Базовая структура React-приложения: Vite, Tailwind, shadcn/ui, роутинг, стейт, i18n, PWA.",
                "sprint": 1,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Инициализировать Vite 6 + React 18 + TypeScript 5.x",
                        "description": (
                            "## Описание\n"
                            "Создать проект: `npm create vite@latest frontend -- --template react-ts`. "
                            "Настроить `tsconfig.json` (strict: true, paths alias `@/*` → `src/*`). "
                            "Настроить `vite.config.ts` с path aliases, proxy `/api` на backend. "
                            "Добавить `eslint` + `@typescript-eslint` + `prettier`. "
                            "Настроить `husky` + `lint-staged` для pre-commit проверок.\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `npm run dev` запускает dev-сервер без ошибок\n"
                            "- [ ] `npm run build` создаёт production bundle без TypeScript ошибок\n"
                            "- [ ] `npm run lint` проходит без предупреждений\n"
                            "- [ ] Alias `@/` работает в imports\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "cd frontend && npm run build 2>&1 | tail -5\n"
                            "# Должно завершиться без ошибок\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Настроить Tailwind CSS 4 + shadcn/ui + Radix UI",
                        "description": (
                            "## Описание\n"
                            "Установить Tailwind CSS 4 и настроить `tailwind.config.ts` с дизайн-токенами из ТЗ §8.1: "
                            "цвета background (#0F0F12), surface (#18181C), border (#2E2E38), акцент (#6366F1). "
                            "Настроить CSS-переменные для тёмной/светлой темы. "
                            "Инициализировать `shadcn/ui` с компонентами: Button, Input, Dialog, Card, Badge, Tabs, Slider. "
                            "Шрифты: Inter (variable) + JetBrains Mono через Google Fonts или self-hosted.\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Tailwind 4 utility классы применяются корректно\n"
                            "- [ ] Тёмная тема активируется через `class=\"dark\"` на `<html>`\n"
                            "- [ ] shadcn Button, Input, Dialog рендерятся корректно\n"
                            "- [ ] Шрифты Inter и JetBrains Mono загружаются\n\n"
                            "## Автоматизированная проверка\n"
                            "Визуальная проверка Storybook или демо-страницы с компонентами."
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Настроить TanStack Router + TanStack Query v5 + Zustand",
                        "description": (
                            "## Описание\n"
                            "Установить и настроить: `@tanstack/react-router` (file-based routing), "
                            "`@tanstack/react-query` v5 с `QueryClient` (staleTime 30s, retry 2), "
                            "`zustand` для глобального UI-стейта. "
                            "Создать базовый layout с RouterProvider. "
                            "Настроить ReactQueryDevtools и TanStack Router devtools только для development. "
                            "Создать первичные маршруты: `/`, `/login`, `/register`.\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Навигация между `/`, `/login`, `/register` работает\n"
                            "- [ ] `useQuery` кэширует данные между рендерами\n"
                            "- [ ] Zustand store персистирует состояние в рамках сессии\n"
                            "- [ ] DevTools отображаются только в dev-режиме\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "// router.test.tsx\n"
                            "test('navigates to login', async () => {\n"
                            "  render(<App />)\n"
                            "  expect(window.location.pathname).toBe('/')\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Настроить i18next (ru/en) и Vite PWA Plugin",
                        "description": (
                            "## Описание\n"
                            "Установить `i18next` + `react-i18next`. "
                            "Создать `src/i18n/ru.json` и `src/i18n/en.json` с базовыми ключами (nav, errors, common). "
                            "Инициализировать i18next с автодетекцией языка браузера, fallback на 'ru'. "
                            "Настроить `vite-plugin-pwa`: name='HabitFlow', short_name='HabitFlow', "
                            "theme_color='#6366F1', background_color='#0F0F12', display='standalone', "
                            "start_url='/', icons 192/512/maskable.\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `useTranslation()` возвращает русские строки по умолчанию\n"
                            "- [ ] Смена языка через `i18n.changeLanguage('en')` работает без перезагрузки\n"
                            "- [ ] `npm run build` генерирует `manifest.webmanifest` и service worker\n"
                            "- [ ] Lighthouse PWA score ≥ 90\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "ls dist/ | grep -E 'manifest|sw'\n"
                            "# Должно найти manifest.webmanifest и sw.js\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 1,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 2: Database & Data Layer
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[DB] Database Schema & Data Layer",
        "description": (
            "Полная схема БД PostgreSQL, SQL-миграции через golang-migrate, "
            "типобезопасный слой запросов через sqlc.\n\n"
            "**Фаза:** Phase 0\n"
            "**Зависимости:** EPIC INFRA должен быть завершён."
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "PostgreSQL Schema & Migrations",
                "description": "SQL-миграции 001-009 по схеме из ТЗ §6.3, интеграция golang-migrate.",
                "sprint": 1,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Миграции 001-005: extensions, users, sessions, recovery_codes, categories",
                        "description": (
                            "## Описание\n"
                            "Написать SQL-миграции (up + down) по схеме из ТЗ §6.3:\n"
                            "- `001_init_extensions`: pgcrypto, pg_trgm\n"
                            "- `002_create_users`: таблица users с индексами (partial WHERE deleted_at IS NULL)\n"
                            "- `003_create_sessions`: sessions с индексами на user_id, expires_at\n"
                            "- `004_create_recovery_codes`: recovery_codes с индексом на user_id\n"
                            "- `005_create_categories`: categories с UNIQUE(user_id, name)\n"
                            "Все FK с ON DELETE CASCADE. Timestamps — TIMESTAMPTZ. PK — UUID DEFAULT gen_random_uuid().\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `migrate up` и `migrate down` проходят без ошибок\n"
                            "- [ ] Все индексы присутствуют (проверить через `\\d+ table_name`)\n"
                            "- [ ] `down`-миграции полностью обратимы\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "# Тест round-trip\n"
                            "migrate -path migrations -database $DSN up\n"
                            "migrate -path migrations -database $DSN down\n"
                            "migrate -path migrations -database $DSN up\n"
                            "echo 'Round-trip OK'\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Миграции 006-009: habits, habit_entries, streak function, audit_log",
                        "description": (
                            "## Описание\n"
                            "Написать SQL-миграции:\n"
                            "- `006_create_habits`: CREATE TYPE habit_type/habit_freq AS ENUM; таблица habits со всеми полями из ТЗ; "
                            "индексы на user_id, category_id, sort_order; GIN индекс на name для pg_trgm\n"
                            "- `007_create_habit_entries`: UNIQUE(habit_id, date); индексы на (habit_id, date DESC), (user_id, date DESC)\n"
                            "- `008_create_streak_function`: PL/pgSQL функция current_streak(p_habit_id, p_today) из ТЗ §6.3\n"
                            "- `009_create_audit_log`: таблица audit_log (Phase 2, может быть NoOp в Phase 1)\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] ENUM типы создаются корректно\n"
                            "- [ ] `SELECT current_streak('some-uuid', CURRENT_DATE)` возвращает 0 на пустой таблице\n"
                            "- [ ] GIN индекс для pg_trgm создан\n"
                            "- [ ] Round-trip (up → down → up) проходит\n\n"
                            "## Автоматизированная проверка\n"
                            "```sql\n"
                            "SELECT current_streak(gen_random_uuid(), CURRENT_DATE); -- должно вернуть 0\n"
                            "SELECT typname FROM pg_type WHERE typtype='e'; -- должно показать habit_type, habit_freq\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Интеграция golang-migrate в автостарт backend",
                        "description": (
                            "## Описание\n"
                            "Подключить `golang-migrate/migrate/v4` с embed файловой системой (`embed.FS`). "
                            "В `cmd/server/main.go` перед стартом HTTP-сервера вызывать `m.Up()`. "
                            "Логировать: количество применённых миграций, текущую версию. "
                            "Идемпотентность: повторный запуск не должен падать. "
                            "При ошибке миграции — exit(1) с понятным сообщением.\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] При первом запуске: все миграции применяются\n"
                            "- [ ] При повторном запуске: `no change` без ошибок\n"
                            "- [ ] Если БД недоступна — понятное сообщение об ошибке\n"
                            "- [ ] Версия миграции выводится в лог\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestMigrations(t *testing.T) {\n"
                            "    db := setupTestDB(t) // testcontainers\n"
                            "    err := runMigrations(db)\n"
                            "    assert.NoError(t, err)\n"
                            "    err = runMigrations(db) // повторно — idempotent\n"
                            "    assert.NoError(t, err)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Настроить sqlc и написать SQL-запросы",
                        "description": (
                            "## Описание\n"
                            "Настроить `sqlc.yaml` (engine: postgresql, emit_prepared_queries: false, output Go). "
                            "Написать `.sql` файлы с аннотациями sqlc:\n"
                            "- `queries/auth.sql`: CreateUser, GetUserByUsername, GetUserByEmail, CreateSession, "
                            "GetSessionByToken, RevokeSession, RevokeAllUserSessions, CreateRecoveryCode, "
                            "GetUnusedRecoveryCodes, MarkRecoveryCodeUsed\n"
                            "- `queries/habits.sql`: CreateHabit, GetHabits, GetHabitByID, UpdateHabit, SoftDeleteHabit, "
                            "ArchiveHabit, ReorderHabits\n"
                            "- `queries/entries.sql`: UpsertEntry, GetEntryByHabitDate, GetEntriesForDateRange\n"
                            "- `queries/stats.sql`: GetCompletionRate, GetHeatmapData, GetCurrentStreak, GetMaxStreak\n"
                            "Запустить `sqlc generate`, убедиться что код компилируется.\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `sqlc generate` выполняется без ошибок\n"
                            "- [ ] Сгенерированный код компилируется (`go build ./...`)\n"
                            "- [ ] Все запросы покрывают API из ТЗ §7.2\n"
                            "- [ ] Нет N+1 запросов в GetBoard (JOIN с entries)\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "sqlc generate && go build ./... && echo 'sqlc OK'\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 3: Authentication & Security
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[AUTH] Authentication & Security",
        "description": (
            "Полная система аутентификации: регистрация, JWT RS256, сессии, refresh rotation, "
            "rate limiting, recovery codes, защита от XSS/CSRF.\n\n"
            "**Фаза:** Phase 0-2\n"
            "**Требования:** AUTH-01 — AUTH-08 из ТЗ §2.1"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "User Registration & Recovery Codes",
                "description": "POST /auth/register с argon2id, генерация и хранение recovery codes.",
                "sprint": 1,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Реализовать POST /api/v1/auth/register",
                        "description": (
                            "## Описание\n"
                            "Реализовать регистрацию (handler → service → repository):\n"
                            "- Валидация: username (3-50 символов, a-zA-Z0-9_), password (min 8 символов, 1 цифра)\n"
                            "- Хэширование пароля через `alexedwards/argon2id` (параметры: memory=64MB, iterations=1, parallelism=2)\n"
                            "- Создание пользователя в БД\n"
                            "- Генерация 8 recovery codes (random 16-char base32), bcrypt-хэши хранятся в recovery_codes\n"
                            "- Ответ 201: `{user: {...}, recovery_codes: [\"...\", ...]}` — коды возвращаются ТОЛЬКО ОДИН РАЗ\n"
                            "- Ошибки: 409 если username/email занят, 422 если невалидные поля\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] 201 при корректных данных, recovery_codes в ответе (8 штук)\n"
                            "- [ ] 409 при дубликате username\n"
                            "- [ ] 422 при password < 8 символов\n"
                            "- [ ] argon2id хэши в БД (начинаются с `$argon2id$`)\n"
                            "- [ ] Повторный запрос НЕ возвращает коды (не хранятся в открытом виде)\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestRegister(t *testing.T) {\n"
                            "    // success\n"
                            "    resp := post('/auth/register', validPayload)\n"
                            "    assert.Equal(t, 201, resp.Code)\n"
                            "    assert.Len(t, resp.Body.RecoveryCodes, 8)\n"
                            "    // duplicate\n"
                            "    resp2 := post('/auth/register', validPayload)\n"
                            "    assert.Equal(t, 409, resp2.Code)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Скрипт генерации RS256 JWT ключей",
                        "description": (
                            "## Описание\n"
                            "Создать `scripts/generate-keys.sh`:\n"
                            "```bash\n"
                            "openssl ecparam -name prime256v1 -genkey -noout -out secrets/jwt.key\n"
                            "openssl ec -in secrets/jwt.key -pubout -out secrets/jwt.pub\n"
                            "```\n"
                            "Добавить `secrets/` в `.gitignore`. "
                            "Задокументировать в README как передавать ключи в Kubernetes Secret. "
                            "Создать `scripts/verify-keys.sh` для проверки что ключевая пара совместима.\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Скрипт создаёт `secrets/jwt.key` и `secrets/jwt.pub`\n"
                            "- [ ] Ключи работают для подписи и верификации JWT RS256\n"
                            "- [ ] `secrets/` в `.gitignore`, случайный commit ключей невозможен\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "bash scripts/generate-keys.sh\n"
                            "openssl ec -in secrets/jwt.key -check && echo 'Key OK'\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 1,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "JWT Login, Refresh & Session Management",
                "description": "POST /auth/login с JWT RS256, refresh rotation, logout, session list.",
                "sprint": 1,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Реализовать POST /auth/login и JWT RS256",
                        "description": (
                            "## Описание\n"
                            "Реализовать `/auth/login`:\n"
                            "- Поиск пользователя по username, argon2id verify\n"
                            "- Access token: JWT RS256, payload `{sub: user_id, exp: now+15m, iat}`, подписан EC private key\n"
                            "- Refresh token: random UUID, bcrypt-хэш в таблице sessions с user_agent, ip_address, expires_at (30 days)\n"
                            "- Ответ: `{access_token, refresh_token, token_type: 'Bearer', expires_in: 900}`\n"
                            "- refresh_token передаётся через HttpOnly Secure SameSite=Strict cookie\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] 200 с валидным JWT при верных credentials\n"
                            "- [ ] 401 при неверном пароле\n"
                            "- [ ] JWT верифицируется public key\n"
                            "- [ ] refresh_token в HttpOnly cookie\n"
                            "- [ ] access_token НЕ в cookie, только в JSON body\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestLogin(t *testing.T) {\n"
                            "    resp := post('/auth/login', {username, password})\n"
                            "    assert.Equal(t, 200, resp.Code)\n"
                            "    token := resp.Body.AccessToken\n"
                            "    claims, err := verifyJWT(token, publicKey)\n"
                            "    assert.NoError(t, err)\n"
                            "    assert.Equal(t, userID, claims.Subject)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Реализовать /auth/refresh с rotation и /auth/logout",
                        "description": (
                            "## Описание\n"
                            "**POST /auth/refresh:**\n"
                            "- Читать refresh_token из HttpOnly cookie\n"
                            "- Verify bcrypt hash против sessions таблицы\n"
                            "- Проверить: не revoked, не expired\n"
                            "- Rotation: пометить старый как revoked, создать новый refresh_token\n"
                            "- Если использован уже revoked токен — немедленно revoke ВСЕ сессии пользователя (token theft detection)\n"
                            "- Выдать новый access_token + refresh_token\n\n"
                            "**POST /auth/logout:** revoke текущей сессии по refresh token\n"
                            "**POST /auth/logout-all:** revoke всех сессий пользователя\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Refresh возвращает новую пару токенов\n"
                            "- [ ] Старый refresh_token после rotation → 401\n"
                            "- [ ] Реиспользование revoked token → все сессии удаляются\n"
                            "- [ ] Logout очищает cookie\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestRefreshRotation(t *testing.T) {\n"
                            "    // Token theft detection\n"
                            "    oldToken := login()\n"
                            "    newToken := refresh(oldToken)  // rotation\n"
                            "    resp := refresh(oldToken)       // reuse old\n"
                            "    assert.Equal(t, 401, resp.Code)\n"
                            "    sessions := listSessions(userID)\n"
                            "    assert.Empty(t, sessions) // все revoked\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Rate limiting middleware и защита /auth/*",
                        "description": (
                            "## Описание\n"
                            "Реализовать IP-based rate limiter (in-memory с sliding window или через Echo middleware): "
                            "5 попыток / 15 минут / IP для всех `/auth/*` эндпоинтов. "
                            "При превышении: 429 Too Many Requests + заголовок `Retry-After: 900`. "
                            "Добавить JWT verification middleware для всех `/api/v1/*` маршрутов. "
                            "Middleware порядок: rate_limit → cors → csp → jwt → handler.\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] 5-я попытка логина проходит, 6-я → 429\n"
                            "- [ ] `Retry-After` заголовок присутствует в 429-ответе\n"
                            "- [ ] `/api/v1/habits` без токена → 401\n"
                            "- [ ] Разные IP не влияют на лимиты друг друга\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestRateLimit(t *testing.T) {\n"
                            "    for i := 0; i < 5; i++ {\n"
                            "        resp := post('/auth/login', wrongCreds)\n"
                            "        assert.Equal(t, 401, resp.Code)\n"
                            "    }\n"
                            "    resp := post('/auth/login', wrongCreds)\n"
                            "    assert.Equal(t, 429, resp.Code)\n"
                            "    assert.NotEmpty(t, resp.Header.Get('Retry-After'))\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 1,
                    },
                    {
                        "type": "Task",
                        "summary": "Recovery codes: /auth/recover и /me/recovery-codes",
                        "description": (
                            "## Описание\n"
                            "**POST /api/v1/auth/recover:**\n"
                            "- Принять `{username, recovery_code}`\n"
                            "- Найти unused коды пользователя, bcrypt.CompareHash\n"
                            "- При совпадении: пометить код как used (used_at = now)\n"
                            "- Выдать access token с флагом `must_change_password: true` в claims\n"
                            "- При следующем запросе к API с таким токеном — 403 с требованием сменить пароль\n\n"
                            "**GET /api/v1/me/recovery-codes:** вернуть `{remaining: N}` (только количество!)\n"
                            "**POST /api/v1/me/recovery-codes:** регенерировать все коды (требует current password)\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Валидный код → 200 + access token с must_change_password\n"
                            "- [ ] Уже использованный код → 401\n"
                            "- [ ] После регенерации старые коды недействительны\n"
                            "- [ ] GET /me/recovery-codes не возвращает сами коды\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestRecoveryCodes(t *testing.T) {\n"
                            "    codes := register()\n"
                            "    resp := post('/auth/recover', {username, code: codes[0]})\n"
                            "    assert.Equal(t, 200, resp.Code)\n"
                            "    resp2 := post('/auth/recover', {username, code: codes[0]}) // reuse\n"
                            "    assert.Equal(t, 401, resp2.Code)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Frontend Authentication UI",
                "description": "Страницы Login/Register, token management в памяти, auto-refresh, protected routes.",
                "sprint": 2,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Создать страницы /login и /register",
                        "description": (
                            "## Описание\n"
                            "**Login page:** форма username + password (React Hook Form + Zod), "
                            "кнопка Submit, error toast при 401, ссылка 'Войти через recovery code'. "
                            "**Register page:** форма username + password + confirm password (Zod refinement), "
                            "после успешной регистрации — модальное окно с recovery codes "
                            "(список из 8 кодов, кнопки 'Скопировать все' и 'Скачать .txt', "
                            "чекбокс 'Я сохранил коды', кнопка Продолжить активируется после чекбокса).\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Login: неверный пароль → error message (не alert)\n"
                            "- [ ] Register: password mismatch → inline Zod error\n"
                            "- [ ] Recovery codes modal открывается после успешной регистрации\n"
                            "- [ ] Кнопка 'Продолжить' неактивна до принятия чекбокса\n"
                            "- [ ] Адаптивный дизайн: работает на iPhone 390px\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('shows error on wrong password', async () => {\n"
                            "  render(<LoginPage />)\n"
                            "  fireEvent.submit(form)\n"
                            "  expect(await screen.findByText(/неверный/i)).toBeInTheDocument()\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "Token management: access в памяти, refresh в cookie, auto-refresh",
                        "description": (
                            "## Описание\n"
                            "Создать `src/api/auth.ts` с:\n"
                            "- `accessToken` хранить в closure (не localStorage, не sessionStorage)\n"
                            "- Interceptor ky: добавлять `Authorization: Bearer {token}` к запросам\n"
                            "- При получении 401: автоматически вызывать `/auth/refresh`, "
                            "обновлять access token в памяти, повторить оригинальный запрос\n"
                            "- Queue pending requests во время refresh (один refresh на всех)\n"
                            "- При failed refresh → редирект на /login\n"
                            "- AuthProvider context: `{user, isLoading, login, logout}`\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] access_token НЕ попадает в localStorage при DevTools инспекции\n"
                            "- [ ] После истечения 15 мин токен обновляется прозрачно\n"
                            "- [ ] Одновременные запросы при expired token → только один refresh вызов\n"
                            "- [ ] Закрытие/открытие вкладки: пользователь остаётся залогиненным (через cookie)\n\n"
                            "## Автоматизированная проверка\n"
                            "Playwright test: login → подождать 15 мин (mocked) → запрос API → убедиться что нет 401."
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 2,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 4: Habit Management
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[HABITS] Habit & Category Management",
        "description": (
            "CRUD привычек трёх типов (boolean/numeric/duration), категории, архивирование, drag&drop сортировка.\n\n"
            "**Фаза:** Phase 1-2\n"
            "**Требования:** HAB-01 — HAB-10 из ТЗ §2.2"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Habit CRUD API (Backend)",
                "description": "Полный REST API для привычек: создание, чтение, обновление, удаление, архивирование, сортировка.",
                "sprint": 2,
                "children": [
                    {
                        "type": "Task",
                        "summary": "POST/GET/PUT/DELETE /api/v1/habits",
                        "description": (
                            "## Описание\n"
                            "Реализовать полный CRUD для привычек:\n"
                            "- `POST /api/v1/habits`: validate (name ≤200, type ∈ {boolean,numeric,duration}, "
                            "frequency ∈ {daily,weekly,custom}), для numeric — требовать target_value и unit; создать в БД\n"
                            "- `GET /api/v1/habits`: фильтрация по `?category=uuid&archived=false|true`, "
                            "сортировка по sort_order\n"
                            "- `GET /api/v1/habits/:id`: 404 если не существует или принадлежит другому пользователю\n"
                            "- `PUT /api/v1/habits/:id`: обновить поля (нельзя менять type после создания)\n"
                            "- `DELETE /api/v1/habits/:id`: soft-delete (deleted_at), каскадное удаление entries\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все 5 операций работают\n"
                            "- [ ] Isolation: пользователь видит только свои привычки\n"
                            "- [ ] Удаление каскадно удаляет habit_entries\n"
                            "- [ ] Попытка изменить type → 400\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestHabitCRUD(t *testing.T) {\n"
                            "    habit := createHabit(t, booleanPayload)\n"
                            "    assert.Equal(t, 'boolean', habit.Type)\n"
                            "    updateHabit(t, habit.ID, {name: 'Updated'})\n"
                            "    deleteHabit(t, habit.ID)\n"
                            "    entries := getEntries(t, habit.ID)\n"
                            "    assert.Empty(t, entries) // cascade\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "PATCH /habits/:id/archive и PATCH /habits/reorder",
                        "description": (
                            "## Описание\n"
                            "**PATCH /habits/:id/archive:**\n"
                            "- Toggle архивирования: `{archived: true|false}`\n"
                            "- При архивировании: `is_archived=true, archived_at=now()`\n"
                            "- При разархивировании: `is_archived=false, archived_at=null`\n"
                            "- Архивированные привычки не появляются в `/board` и в default GET /habits\n\n"
                            "**PATCH /habits/reorder:**\n"
                            "- Принимает `{ids: [uuid, uuid, ...]}` в нужном порядке\n"
                            "- Обновляет sort_order для каждой привычки\n"
                            "- Транзакция: либо все обновляются, либо ни одна\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Архивированная привычка исчезает из board и default list\n"
                            "- [ ] Разархивированная — снова появляется\n"
                            "- [ ] Reorder: порядок после запроса соответствует переданному массиву\n"
                            "- [ ] Reorder с чужими habit IDs → 403\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestArchiveAndReorder(t *testing.T) {\n"
                            "    h1, h2, h3 := createThreeHabits(t)\n"
                            "    reorder(t, [h3.ID, h1.ID, h2.ID])\n"
                            "    habits := getHabits(t)\n"
                            "    assert.Equal(t, h3.ID, habits[0].ID)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "CRUD /api/v1/categories + reorder",
                        "description": (
                            "## Описание\n"
                            "Реализовать полный CRUD для категорий:\n"
                            "- `POST /categories`: name ≤100, color (hex #RRGGBB), icon (lucide name)\n"
                            "- `GET /categories`: отсортированные по sort_order\n"
                            "- `PUT /categories/:id`: обновить name/color/icon\n"
                            "- `DELETE /categories/:id`: удалить; связанные habits.category_id → NULL (ON DELETE SET NULL)\n"
                            "- `PATCH /categories/reorder`: массив IDs\n"
                            "- UNIQUE(user_id, name): 409 при дубликате имени\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все 5 операций + reorder работают\n"
                            "- [ ] Удаление категории → привычки остаются, category_id = null\n"
                            "- [ ] 409 при дублирующемся имени\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestCategoryDelete(t *testing.T) {\n"
                            "    cat := createCategory(t)\n"
                            "    habit := createHabit(t, {category_id: cat.ID})\n"
                            "    deleteCategory(t, cat.ID)\n"
                            "    h := getHabit(t, habit.ID)\n"
                            "    assert.Nil(t, h.CategoryID)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Habit Management UI (Frontend)",
                "description": "Страница управления привычками: список, форма создания/редактирования, drag&drop, архив.",
                "sprint": 2,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Страница /habits: список с категориями и архивом",
                        "description": (
                            "## Описание\n"
                            "Создать страницу `/habits` согласно макету из ТЗ §8.3 (Экран 2):\n"
                            "- Заголовок 'Привычки' + кнопка '+ Новая'\n"
                            "- Табы категорий (горизонтальный scroll если много)\n"
                            "- Список привычек с: handle для drag (≡), иконка, название, текущий streak 🔥, меню '···'\n"
                            "- Секция 'Архив (N)' — коллапсируемая, показывает архивированные\n"
                            "- Меню '···' на привычке: Редактировать, Архивировать, Удалить (с confirm dialog)\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Таб 'Все' показывает все неархивированные привычки\n"
                            "- [ ] Таб категории фильтрует корректно\n"
                            "- [ ] Архивированные привычки скрыты по умолчанию\n"
                            "- [ ] Confirm dialog перед удалением\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('archive hides from list', async () => {\n"
                            "  render(<HabitsPage />)\n"
                            "  fireEvent.click(archiveButton)\n"
                            "  expect(habitRow).not.toBeVisible()\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "HabitForm dialog: создание и редактирование всех типов привычек",
                        "description": (
                            "## Описание\n"
                            "Создать shadcn Dialog с формой (React Hook Form + Zod):\n"
                            "- Поля: Name*, Type* (radio: boolean/numeric/duration), Category (select), "
                            "Color (color picker 10 вариантов), Icon (grid из Lucide иконок)\n"
                            "- Условные поля при type=numeric: Target Value* + Unit*\n"
                            "- Условные поля при type=duration: без дополнительных (unit='мин' фиксирован)\n"
                            "- Frequency: ежедневно / конкретные дни (чекбоксы Пн-Вс) / N раз в неделю\n"
                            "- Zod схема валидирует все комбинации\n"
                            "- Режим редактирования: поле type disabled\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Создание boolean привычки: форма принимается, привычка в списке\n"
                            "- [ ] Создание numeric без target_value → Zod ошибка\n"
                            "- [ ] Редактирование: type поле задизаблено\n"
                            "- [ ] Форма сбрасывается при закрытии dialog\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('requires target for numeric', async () => {\n"
                            "  selectType('numeric')\n"
                            "  submitForm()\n"
                            "  expect(screen.getByText(/цель обязательна/i)).toBeVisible()\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "Drag & Drop сортировка привычек (@dnd-kit)",
                        "description": (
                            "## Описание\n"
                            "Реализовать drag & drop с `@dnd-kit/core` + `@dnd-kit/sortable`:\n"
                            "- Drag handle (≡ иконка) на каждой строке привычки\n"
                            "- Визуальный placeholder при dragging\n"
                            "- Оптимистичное обновление порядка (UI сразу, API вызов после drop)\n"
                            "- При ошибке API — откат к предыдущему порядку\n"
                            "- Touch-friendly: работает на iOS (pointer events)\n"
                            "- Вызов `PATCH /habits/reorder` после drop с новым порядком ID\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Drag & drop работает мышью\n"
                            "- [ ] Drag & drop работает на тачскрине (iPhone)\n"
                            "- [ ] Порядок сохраняется после перезагрузки страницы\n"
                            "- [ ] Placeholder виден при dragging\n\n"
                            "## Автоматизированная проверка\n"
                            "Playwright test: drag habit 3 на позицию 1, reload, проверить порядок."
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 3,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 5: Tracking Board
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[BOARD] Daily Tracking Board",
        "description": (
            "Главный экран приложения: матрица привычки × день. "
            "Отметка выполнения, навигация по датам, окно редактирования, стрики.\n\n"
            "**Фаза:** Phase 1\n"
            "**Требования:** TRK-01 — TRK-13 из ТЗ §2.3"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Board & Entries API (Backend)",
                "description": "GET /board/:date с is_editable, POST /entries с upsert, edit window validation.",
                "sprint": 2,
                "children": [
                    {
                        "type": "Task",
                        "summary": "GET /api/v1/board/:date — главный эндпоинт доски",
                        "description": (
                            "## Описание\n"
                            "Реализовать `GET /api/v1/board/:date` (формат YYYY-MM-DD):\n"
                            "- Определить дату в timezone пользователя\n"
                            "- `is_editable`: true если дата ≥ (today - edit_window_days) и ≤ today\n"
                            "- Загрузить все активные (неархивированные) привычки пользователя\n"
                            "- JOIN с habit_entries для данной даты\n"
                            "- Для каждой привычки: `streak` = current_streak() из БД\n"
                            "- `progress`: `{done: N, total: M}` (done = completed entries)\n"
                            "- Ответ строго по модели из ТЗ §7.3\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Сегодня: is_editable=true\n"
                            "- [ ] Вчера с window=1: is_editable=true\n"
                            "- [ ] 2 дня назад с window=1: is_editable=false\n"
                            "- [ ] Завтра: 400 Bad Request (нельзя смотреть будущее)\n"
                            "- [ ] progress.total равен кол-ву активных привычек\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestBoardDate(t *testing.T) {\n"
                            "    today := date.Today(userTZ)\n"
                            "    board := getBoard(t, today.Format('2006-01-02'))\n"
                            "    assert.True(t, board.IsEditable)\n"
                            "    assert.Equal(t, len(activeHabits), board.Progress.Total)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "POST/PUT/DELETE /api/v1/entries + edit window validation",
                        "description": (
                            "## Описание\n"
                            "**POST /entries (UPSERT):**\n"
                            "- Тело: `{habit_id, date, completed, value, note}`\n"
                            "- Проверить edit window: дата ≥ (today - edit_window_days) И ≤ today → иначе 403\n"
                            "- UPSERT: INSERT ... ON CONFLICT (habit_id, date) DO UPDATE\n"
                            "- Для boolean: value игнорируется, completed = true/false\n"
                            "- Для numeric: если value ≥ target_value → completed = true\n"
                            "- Для duration: если value > 0 → completed = true\n\n"
                            "**PUT /entries/:id:** обновить value и/или note\n"
                            "**DELETE /entries/:id:** установить completed=false, value=null, note=null\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Запись на сегодня → 200/201\n"
                            "- [ ] Запись на 2 дня назад (window=1) → 403\n"
                            "- [ ] Запись на завтра → 403\n"
                            "- [ ] numeric: value=15, target=20 → completed=false; value=20 → completed=true\n"
                            "- [ ] UPSERT: повторный POST обновляет существующую запись\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestEditWindow(t *testing.T) {\n"
                            "    // window = 1 (default)\n"
                            "    testCases := []struct{date string; expectedCode int}{\n"
                            "        {today, 201},\n"
                            "        {yesterday, 201},\n"
                            "        {dayBeforeYesterday, 403},\n"
                            "        {tomorrow, 403},\n"
                            "    }\n"
                            "    for _, tc := range testCases {\n"
                            "        resp := postEntry(t, habitID, tc.date)\n"
                            "        assert.Equal(t, tc.expectedCode, resp.Code)\n"
                            "    }\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "GET /habits/:id/streak — текущий и максимальный стрик",
                        "description": (
                            "## Описание\n"
                            "Реализовать `GET /api/v1/habits/:id/streak`:\n"
                            "- Текущий стрик: вызвать PL/pgSQL функцию `current_streak(habit_id, today_in_user_tz)`\n"
                            "- Максимальный стрик: вычислить в Go (загрузить все completed entries, отсортировать по дате, "
                            "найти самую длинную непрерывную последовательность)\n"
                            "- Ответ: `{current: N, max: M, habit_id: uuid}`\n"
                            "- Для numeric/duration: 'completed' = value ≥ target (или value > 0 для duration)\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] 5 подряд выполненных дней → current=5\n"
                            "- [ ] Пропуск на 3-й день → current=0 (стрик сбрасывается)\n"
                            "- [ ] max всегда ≥ current\n"
                            "- [ ] Для numeric: value < target → не считается в стрик\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestStreak(t *testing.T) {\n"
                            "    // Заполнить 5 дней подряд\n"
                            "    for i := 4; i >= 0; i-- {\n"
                            "        createEntry(t, habitID, today.AddDate(0,0,-i), true)\n"
                            "    }\n"
                            "    streak := getStreak(t, habitID)\n"
                            "    assert.Equal(t, 5, streak.Current)\n"
                            "    assert.Equal(t, 5, streak.Max)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Board UI (Frontend)",
                "description": "Главный экран: HabitRow по типам, DateNavBar, прогресс, режим read-only, swipe, streak pulse.",
                "sprint": 2,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Board page и DateNavBar компонент",
                        "description": (
                            "## Описание\n"
                            "Создать главную страницу `/board` (и редирект с `/`):\n"
                            "- Использовать `useQuery` для `GET /board/:date`\n"
                            "- Skeleton loading (не спиннер) пока данные загружаются\n"
                            "**DateNavBar компонент:**\n"
                            "- Формат даты: 'Вс, 21 июня' (i18n aware, неделя из настроек)\n"
                            "- Стрелка ← : активна всегда, при нажатии открывает предыдущий день\n"
                            "- Стрелка → : активна только если текущая дата < today\n"
                            "- Кнопка 'Сегодня': появляется если просматриваемая дата ≠ today\n"
                            "- DayProgress: `████████░░ 5 из 7` (progress bar + текст)\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Навигация ← → меняет дату в URL и перезагружает данные\n"
                            "- [ ] Стрелка → недоступна на today\n"
                            "- [ ] Skeleton отображается при загрузке\n"
                            "- [ ] 'Сегодня' возвращает к текущей дате\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('forward arrow disabled on today', () => {\n"
                            "  render(<DateNavBar date={today} />)\n"
                            "  expect(screen.getByRole('button', {name: /вперёд/i})).toBeDisabled()\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "HabitRow: BooleanToggle, NumericInput, DurationInput компоненты",
                        "description": (
                            "## Описание\n"
                            "Создать компонент `HabitRow` с условным рендерингом по `habit.type`:\n\n"
                            "**BooleanHabitToggle:**\n"
                            "- Большая круглая кнопка с иконкой (≥44pt)\n"
                            "- Состояния: off (border), on (filled accent color, checkmark)\n"
                            "- При click: bounce анимация 50ms + цветовой flash\n"
                            "- Оптимистичное обновление через `useMutation` + rollback при ошибке\n\n"
                            "**NumericHabitInput:**\n"
                            "- Шаблон: [–] [текущее значение / цель] [+]\n"
                            "- Inline редактирование по tap на число\n"
                            "- inputmode='decimal' для мобильного\n\n"
                            "**DurationHabitInput:**\n"
                            "- Input с плейсхолдером '0 мин'\n"
                            "- inputmode='numeric'\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Boolean: toggle работает, анимация воспроизводится\n"
                            "- [ ] Numeric: [–][+] кнопки изменяют значение на 1\n"
                            "- [ ] Все touch targets ≥ 44×44pt\n"
                            "- [ ] Оптимистичное обновление: UI меняется мгновенно\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('boolean toggle calls API', async () => {\n"
                            "  const mockMutate = jest.fn()\n"
                            "  render(<BooleanHabitToggle onToggle={mockMutate} />)\n"
                            "  fireEvent.click(toggleButton)\n"
                            "  expect(mockMutate).toHaveBeenCalledWith({completed: true})\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "Read-only режим и swipe навигация",
                        "description": (
                            "## Описание\n"
                            "**Read-only режим:**\n"
                            "- Если `board.is_editable === false`: все кнопки disabled, иконка 🔒 рядом с датой\n"
                            "- Визуально: opacity 0.5 на контролах, cursor: not-allowed\n"
                            "- Tooltip при hover: 'Вне окна редактирования'\n\n"
                            "**Swipe навигация:**\n"
                            "- Слушать touchstart + touchend на всём экране\n"
                            "- Swipe влево (deltaX < -50): перейти к следующему дню (если < today)\n"
                            "- Swipe вправо (deltaX > 50): перейти к предыдущему дню\n"
                            "- Анимация slide 100ms ease-out при переходе\n"
                            "- Нет конфликта с вертикальным скроллом (проверять deltaY vs deltaX)\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Дата за пределами edit_window: все контролы задизаблены + 🔒\n"
                            "- [ ] Swipe работает на iPhone (протестировать на real device)\n"
                            "- [ ] Swipe не перехватывает вертикальный скролл\n"
                            "- [ ] Slide-анимация плавная\n\n"
                            "## Автоматизированная проверка\n"
                            "Playwright mobile.spec.ts: симуляция swipe events на iPhone 14 viewport."
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "Streak Pulse анимация и финальный polish Board",
                        "description": (
                            "## Описание\n"
                            "Согласно ТЗ §8.1: при текущем стрике ≥7 дней — "
                            "иконка привычки получает мягкое свечение в цвет привычки.\n"
                            "```css\n"
                            "@keyframes streakPulse {\n"
                            "  0%, 100% { box-shadow: 0 0 0 0 var(--habit-color-alpha); }\n"
                            "  50% { box-shadow: 0 0 12px 4px var(--habit-color-alpha); }\n"
                            "}\n"
                            "```\n"
                            "CSS-переменная `--habit-color-alpha` = цвет привычки с alpha=0.4.\n"
                            "Анимация применяется только на иконку, не на всю строку.\n"
                            "Финальный polish: выравнивание, правильные отступы, separator между привычками.\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Стрик < 7 → нет свечения\n"
                            "- [ ] Стрик ≥ 7 → иконка светится в цвет привычки\n"
                            "- [ ] Анимация плавная, не вызывает layout reflow\n"
                            "- [ ] Работает в тёмной и светлой теме\n\n"
                            "## Автоматизированная проверка\n"
                            "Визуальный регрессионный тест (Playwright screenshot comparison)."
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 3,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 6: Statistics & Analytics
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[STATS] Statistics & Analytics",
        "description": (
            "Аналитика: completion rate, стрики, тепловые карты, линейные графики.\n\n"
            "**Фаза:** Phase 3\n"
            "**Требования:** STAT-01 — STAT-06 из ТЗ §2.4"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Statistics API (Backend)",
                "description": "Dashboard, overview stats, heatmap, per-habit stats эндпоинты.",
                "sprint": 4,
                "children": [
                    {
                        "type": "Task",
                        "summary": "GET /dashboard и GET /stats/overview",
                        "description": (
                            "## Описание\n"
                            "**GET /api/v1/dashboard:**\n"
                            "- today_progress: `{done, total}` для текущего дня\n"
                            "- top_streaks: топ-5 привычек по current_streak\n"
                            "- completion_7d: overall completion за 7 дней (%)\n"
                            "- Всё в одном SQL-запросе (или 2-3 быстрых)\n\n"
                            "**GET /api/v1/stats/overview:**\n"
                            "- `?period=7d|30d|90d|custom&from=YYYY-MM-DD&to=YYYY-MM-DD`\n"
                            "- Per-habit completion rate: `{habit_id, name, color, completion_rate, total_days, completed_days}`\n"
                            "- Overall completion rate\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Dashboard отвечает < 100ms\n"
                            "- [ ] completion_rate = completed_days / total_possible_days (с учётом frequency)\n"
                            "- [ ] period=custom без from/to → 400\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestDashboard(t *testing.T) {\n"
                            "    // Создать 3 привычки, отметить 2 сегодня\n"
                            "    dashboard := getDashboard(t)\n"
                            "    assert.Equal(t, 2, dashboard.TodayProgress.Done)\n"
                            "    assert.Equal(t, 3, dashboard.TodayProgress.Total)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 4,
                    },
                    {
                        "type": "Task",
                        "summary": "GET /stats/heatmap и GET /habits/:id/stats",
                        "description": (
                            "## Описание\n"
                            "**GET /api/v1/stats/heatmap?year=YYYY:**\n"
                            "- Вернуть 365 (или 366) объектов: `{date, completion_rate}` для каждого дня года\n"
                            "- completion_rate = (завершённых привычек / активных привычек) * 100\n"
                            "- Включить только дни ≤ today\n\n"
                            "**GET /api/v1/habits/:id/stats?from=&to=:**\n"
                            "- completion_rate за период\n"
                            "- avg_value (для numeric/duration)\n"
                            "- daily_data: массив `{date, completed, value}` для каждого дня\n"
                            "- current_streak, max_streak\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] heatmap возвращает ровно кол-во дней с 1 января по today\n"
                            "- [ ] completion_rate ∈ [0, 100]\n"
                            "- [ ] stats для пустого периода: completion_rate=0, avg_value=null\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "heatmap := getHeatmap(t, 2026)\n"
                            "assert.LessOrEqual(t, len(heatmap.Days), 366)\n"
                            "for _, day := range heatmap.Days {\n"
                            "    assert.GreaterOrEqual(t, day.CompletionRate, 0.0)\n"
                            "    assert.LessOrEqual(t, day.CompletionRate, 100.0)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 4,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Statistics UI (Frontend)",
                "description": "Страница статистики: completion cards, line chart (Recharts), year heatmap, habit detail.",
                "sprint": 4,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Страница /stats и CompletionRateCard",
                        "description": (
                            "## Описание\n"
                            "Создать страницу `/stats`:\n"
                            "- 3 карточки completion rate: 7 дней / 30 дней / 90 дней\n"
                            "- Каждая карточка: большое число % + тренд (↑↓) по сравнению с предыдущим периодом\n"
                            "- Топ-5 привычек по стрику (иконка, название, стрик 🔥)\n"
                            "- Period selector для переключения периода\n"
                            "- Skeleton loading\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] 3 карточки с корректными данными\n"
                            "- [ ] Тренд показывает ↑ при улучшении\n"
                            "- [ ] Работает при 0 привычках (empty state)\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('shows 3 rate cards', () => {\n"
                            "  render(<StatsPage />)\n"
                            "  expect(screen.getAllByTestId('rate-card')).toHaveLength(3)\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 4,
                    },
                    {
                        "type": "Task",
                        "summary": "YearHeatmap (52×7 calendar) и DailyLineChart компоненты",
                        "description": (
                            "## Описание\n"
                            "**YearHeatmap:**\n"
                            "- 52 колонки × 7 строк (Пн-Вс)\n"
                            "- Цвет ячейки: от серого (#2E2E38) при 0% до акцента (#6366F1) при 100%\n"
                            "- 4 уровня интенсивности: 0%, 1-25%, 26-75%, 76-100%\n"
                            "- Tooltip при hover: дата + процент\n"
                            "- Подписи месяцев сверху\n"
                            "- Скроллируемый на мобиле (overflow-x: auto)\n\n"
                            "**DailyLineChart (Recharts):**\n"
                            "- X ось: даты последних 30 дней\n"
                            "- Y ось: completion % 0-100\n"
                            "- ResponsiveContainer, тёмная тема\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Ровно 365 ячеек для невисокосного года\n"
                            "- [ ] Первая колонка начинается с правильного дня недели\n"
                            "- [ ] Tooltip показывает правильную дату\n"
                            "- [ ] Line chart отображает корректные данные\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('renders 365 cells', () => {\n"
                            "  const data = generateYearData(2025)\n"
                            "  render(<YearHeatmap data={data} />)\n"
                            "  expect(screen.getAllByRole('cell')).toHaveLength(365)\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 4,
                    },
                    {
                        "type": "Task",
                        "summary": "Страница /habits/:id — детали привычки с heatmap",
                        "description": (
                            "## Описание\n"
                            "Создать страницу деталей привычки согласно макету ТЗ §8.3 (Экран 3):\n"
                            "- Header: ← иконка + название + кнопка редактировать ✎\n"
                            "- Карточки: Текущий стрик 🔥, Максимум, За 30 дней %\n"
                            "- Месячный heatmap (GitHub-style) с навигацией месяц ← →\n"
                            "- Collapsible: 'График за 90 дней' (LineChart)\n"
                            "- Для numeric: avg_value за текущий месяц\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Страница открывается за < 500ms\n"
                            "- [ ] Стрики корректно отображаются\n"
                            "- [ ] Heatmap соответствует реальным данным\n"
                            "- [ ] Навигация по месяцам в heatmap работает\n\n"
                            "## Автоматизированная проверка\n"
                            "Playwright: открыть habit detail, проверить наличие всех секций."
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 4,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 7: User Profile & Settings
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[PROFILE] User Profile & Settings",
        "description": (
            "Профиль пользователя, смена пароля, настройки: тема, timezone, язык, edit_window.\n\n"
            "**Фаза:** Phase 1-5\n"
            "**Требования:** SET-01 — SET-06 из ТЗ §2.5"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Profile API (Backend)",
                "description": "GET/PATCH /me, смена пароля, удаление аккаунта.",
                "sprint": 2,
                "children": [
                    {
                        "type": "Task",
                        "summary": "GET/PATCH /api/v1/me и смена пароля",
                        "description": (
                            "## Описание\n"
                            "**GET /api/v1/me:** вернуть профиль без password_hash\n"
                            "**PATCH /api/v1/me:** обновить `display_name, timezone, week_starts_on, theme, language, edit_window_days`\n"
                            "- timezone: валидировать через `time.LoadLocation()`\n"
                            "- edit_window_days: BETWEEN 1 AND 30\n"
                            "- theme: ∈ {light, dark, system}\n"
                            "**PATCH /api/v1/me/password:** старый пароль + новый пароль\n"
                            "- Verify старый через argon2id\n"
                            "- Hash новый через argon2id\n"
                            "- Revoke все сессии кроме текущей\n"
                            "**DELETE /api/v1/me:** пароль + soft-delete пользователя\n\n"
                            "## Исполнитель\n💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] PATCH /me обновляет только переданные поля\n"
                            "- [ ] Невалидный timezone → 400\n"
                            "- [ ] Смена пароля инвалидирует другие сессии\n"
                            "- [ ] DELETE /me требует верный пароль\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestProfileUpdate(t *testing.T) {\n"
                            "    patch('/me', {edit_window_days: 7})\n"
                            "    me := get('/me')\n"
                            "    assert.Equal(t, 7, me.EditWindowDays)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "Backend Developer",
                        "sprint": 2,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Settings Page (Frontend)",
                "description": "Страница настроек: тема, timezone, язык, edit_window, смена пароля.",
                "sprint": 3,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Создать страницу /settings со всеми разделами",
                        "description": (
                            "## Описание\n"
                            "Создать `/settings` с секциями:\n"
                            "**Профиль:** display_name input, сохранить\n"
                            "**Отображение:**\n"
                            "- Тема: 3 кнопки (Светлая☀️ / Тёмная🌙 / Системная💻)\n"
                            "- Первый день недели: toggle Пн/Вс\n"
                            "- Язык: select ru/en\n"
                            "**Трекинг:**\n"
                            "- Timezone: searchable select\n"
                            "- Окно редактирования: slider 1-30 + live label 'Можно редактировать N дней назад'\n"
                            "**Безопасность:** форма смены пароля (current + new + confirm)\n"
                            "**Опасная зона:** красная кнопка 'Удалить аккаунт' → confirm dialog с паролем\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Тема переключается мгновенно (без перезагрузки)\n"
                            "- [ ] Slider edit_window обновляет label в реальном времени\n"
                            "- [ ] Смена языка меняет весь UI без перезагрузки\n"
                            "- [ ] Delete account: требует ввести пароль в confirm dialog\n\n"
                            "## Автоматизированная проверка\n"
                            "```tsx\n"
                            "test('theme toggle changes class', () => {\n"
                            "  fireEvent.click(darkThemeButton)\n"
                            "  expect(document.documentElement.classList.contains('dark')).toBe(true)\n"
                            "})\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 3,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 8: Monitoring & Observability
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[OPS] Monitoring, Logging & Alerting",
        "description": (
            "Prometheus метрики, Grafana dashboards, Loki логи, Alertmanager.\n\n"
            "**Фаза:** Phase 4\n"
            "**Требования:** ТЗ §10"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Prometheus Metrics & Business KPIs",
                "description": "Реализация всех метрик из ТЗ §10.1 в backend.",
                "sprint": 5,
                "children": [
                    {
                        "type": "Task",
                        "summary": "HTTP и бизнес-метрики в backend",
                        "description": (
                            "## Описание\n"
                            "Реализовать все метрики из ТЗ §10.1:\n"
                            "**HTTP метрики (middleware):**\n"
                            "- `habitflow_http_requests_total{method, path, status}` — counter\n"
                            "- `habitflow_http_request_duration_seconds{method, path}` — histogram "
                            "(buckets: 10ms, 50ms, 100ms, 200ms, 500ms, 1s, 5s)\n"
                            "- `habitflow_http_requests_in_flight` — gauge\n"
                            "**Бизнес-метрики:**\n"
                            "- `habitflow_habit_entries_created_total{type}` — counter\n"
                            "- `habitflow_active_users_total` — gauge (UPDATE каждые 5 мин)\n"
                            "- `habitflow_habits_total{archived}` — gauge\n"
                            "- `habitflow_streak_current_max` — gauge (максимальный стрик среди всех пользователей)\n"
                            "**DB pool:**\n"
                            "- `habitflow_db_connections_total` — gauge\n"
                            "- `habitflow_db_query_duration_seconds{query}` — histogram\n\n"
                            "## Исполнитель\n💻 Backend Developer / 🏗️ SRE\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все метрики видны в `/metrics`\n"
                            "- [ ] После создания entry: counter `habitflow_habit_entries_created_total` увеличивается\n"
                            "- [ ] Гистограммы имеют правильные buckets\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "curl -s :9090/metrics | grep -E '^habitflow_' | wc -l\n"
                            "# Должно быть ≥ 10 уникальных метрик\n"
                            "```"
                        ),
                        "expert": "Backend Developer / SRE",
                        "sprint": 5,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Grafana Dashboards & Loki Logging",
                "description": "3 дашборда Grafana, структурированные логи, Alloy + Loki, AlertManager.",
                "sprint": 5,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Создать 3 Grafana dashboard JSON (Application, Business, Infrastructure)",
                        "description": (
                            "## Описание\n"
                            "Создать JSON файлы для Grafana dashboards согласно ТЗ §10.2:\n"
                            "**Dashboard 1 - Application Overview:**\n"
                            "- RPS по эндпоинтам (line chart)\n"
                            "- Latency p50/p95/p99 (line chart)\n"
                            "- Error rate 5xx (stat + time series)\n"
                            "- Active users (gauge), DB pool utilization\n"
                            "**Dashboard 2 - Business Metrics:**\n"
                            "- Новые entries/день, top привычки, completion rate, типы привычек (pie)\n"
                            "**Dashboard 3 - Infrastructure:**\n"
                            "- CPU/Memory по подам, PVC utilization, pod restarts\n"
                            "Хранить в `helm/habitflow/dashboards/` → монтировать через ConfigMap.\n\n"
                            "## Исполнитель\n🏗️ SRE\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все 3 дашборда импортируются в Grafana без ошибок\n"
                            "- [ ] Все панели показывают данные в docker-compose окружении\n"
                            "- [ ] Grafana DataSource настроен на Prometheus\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "# Проверить что JSON валиден\n"
                            "for f in helm/habitflow/dashboards/*.json; do\n"
                            "  python3 -m json.tool $f > /dev/null && echo \"$f OK\"\n"
                            "done\n"
                            "```"
                        ),
                        "expert": "SRE",
                        "sprint": 5,
                    },
                    {
                        "type": "Task",
                        "summary": "Настроить Grafana Alloy + Loki и Alertmanager rules",
                        "description": (
                            "## Описание\n"
                            "**Loki интеграция:**\n"
                            "- Настроить Grafana Alloy DaemonSet для сбора логов с подов (по label `app=habitflow-*`)\n"
                            "- Loki deployment в namespace monitoring\n"
                            "- Grafana datasource Loki\n"
                            "- Задокументировать LogQL запросы из ТЗ §10.3 в runbook\n\n"
                            "**Alertmanager:**\n"
                            "- Создать `alerts/habitflow.yaml` с rules из ТЗ §10.4:\n"
                            "HighErrorRate, HighLatency, DBConnectionsExhausted, PodNotReady, DiskAlmostFull\n"
                            "- Интегрировать в Helm chart\n\n"
                            "## Исполнитель\n🏗️ SRE\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Логи видны в Grafana Explore (Loki datasource)\n"
                            "- [ ] Фильтр `{app='habitflow-backend'} | json | level='error'` работает\n"
                            "- [ ] Все 5 alert rules созданы и visible в Alertmanager UI\n"
                            "- [ ] Стрельба тестового alert'а через `amtool alert add`\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "promtool check rules alerts/habitflow.yaml && echo 'Rules OK'\n"
                            "```"
                        ),
                        "expert": "SRE",
                        "sprint": 5,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 9: Kubernetes & Helm Deployment
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[K8S] Kubernetes & Helm Deployment",
        "description": (
            "Docker образы, Helm chart, K3s deployment, cert-manager, backup CronJob, RBAC.\n\n"
            "**Фаза:** Phase 4\n"
            "**Требования:** ТЗ §11"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Docker Images (Backend & Frontend)",
                "description": "Multi-stage Dockerfiles, Nginx config, ENV injection для frontend.",
                "sprint": 5,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Backend Dockerfile (multi-stage, scratch final image)",
                        "description": (
                            "## Описание\n"
                            "Создать `backend/Dockerfile` строго по ТЗ §11.4:\n"
                            "```dockerfile\n"
                            "FROM golang:1.23-alpine AS builder\n"
                            "# ... go build CGO_ENABLED=0 с -ldflags '-s -w -X main.Version=...'\n"
                            "FROM scratch\n"
                            "# только бинарник + SSL certs + migrations\n"
                            "```\n"
                            "- `USER 1000` в final image\n"
                            "- EXPOSE 8080 9090\n"
                            "- `.dockerignore`: исключить vendor/, *.md, tests\n"
                            "- Build arg: `VERSION` (default: dev)\n"
                            "- Проверить что image size < 30MB\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `docker build` без ошибок\n"
                            "- [ ] Image size ≤ 30MB\n"
                            "- [ ] Container запускается без root (USER 1000)\n"
                            "- [ ] `docker run --read-only` работает\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "docker build -t backend:test backend/\n"
                            "SIZE=$(docker image inspect backend:test --format '{{.Size}}')\n"
                            "[ $SIZE -lt 31457280 ] && echo 'Size OK' || echo 'Too large'\n"
                            "docker run --rm --read-only backend:test /server --version\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                    {
                        "type": "Task",
                        "summary": "Frontend Dockerfile + nginx.conf + docker-entrypoint.sh",
                        "description": (
                            "## Описание\n"
                            "**Dockerfile:** node:22-alpine builder → nginx:1.27-alpine final\n"
                            "**nginx.conf:**\n"
                            "- SPA routing: `try_files $uri $uri/ /index.html`\n"
                            "- `/api/` proxy → backend service\n"
                            "- gzip on, cache headers для статики (1 год для хэшированных assets)\n"
                            "- Security headers: X-Frame-Options, X-Content-Type-Options\n"
                            "**docker-entrypoint.sh:**\n"
                            "- При старте: sed-ом вставить `window.__ENV__={...}` из ENV переменных\n"
                            "- в `<head>` index.html перед другими скриптами\n"
                            "- ENV: `VITE_API_URL`, `VITE_APP_VERSION`\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `window.__ENV__.VITE_API_URL` доступен в браузере после запуска\n"
                            "- [ ] SPA routing: прямой URL `/habits` отдаёт index.html\n"
                            "- [ ] Статические assets кэшируются\n"
                            "- [ ] Image size ≤ 50MB\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "docker run -e VITE_API_URL=http://backend:8080 frontend:test\n"
                            "curl -s http://localhost:3000 | grep 'window.__ENV__'\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Helm Chart — полная реализация",
                "description": "Полный Helm chart по ТЗ §11 с backend/frontend/ingress/backup/monitoring.",
                "sprint": 5,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Helm chart core: Chart.yaml, values.yaml, _helpers.tpl, namespace",
                        "description": (
                            "## Описание\n"
                            "Инициализировать Helm chart структуру:\n"
                            "- `Chart.yaml`: name, version, appVersion, dependencies (bitnami/postgresql 15.x)\n"
                            "- `values.yaml`: полная конфигурация по ТЗ §11.2 со всеми параметрами\n"
                            "- `values.production.yaml`: переопределения для homelab\n"
                            "- `_helpers.tpl`: fullname, labels, selectorLabels, postgresql host\n"
                            "- `templates/namespace.yaml`\n"
                            "- `templates/configmap-app.yaml` (non-secret config)\n"
                            "- `NOTES.txt` с инструкцией post-install\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `helm lint` без ошибок и warnings\n"
                            "- [ ] `helm template` генерирует валидный YAML\n"
                            "- [ ] `helm dependency update` скачивает postgresql chart\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "helm dependency update helm/habitflow\n"
                            "helm lint helm/habitflow\n"
                            "helm template habitflow helm/habitflow | kubeval --strict\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                    {
                        "type": "Task",
                        "summary": "Backend Deployment, Service, HPA, PDB, ServiceMonitor шаблоны",
                        "description": (
                            "## Описание\n"
                            "Создать templates/backend/:\n"
                            "- `deployment.yaml`: строго по ТЗ §11.3 (securityContext: runAsNonRoot, readOnlyRootFilesystem, "
                            "capabilities: DROP ALL, liveness/readiness probes, resources из values)\n"
                            "- `service.yaml`: ClusterIP, ports 8080 (http) + 9090 (metrics)\n"
                            "- `hpa.yaml`: min=1, max=3, targetCPU=70% (если hpa.enabled=true)\n"
                            "- `pdb.yaml`: minAvailable=1 (для zero-downtime rolling update)\n"
                            "- `servicemonitor.yaml`: scrape /metrics на порту 9090 каждые 30s\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Pod запускается с securityContext (runAsUser: 1000)\n"
                            "- [ ] readOnlyRootFilesystem: true (потребует tmpdir для logs если нужно)\n"
                            "- [ ] HPA реагирует на CPU нагрузку\n"
                            "- [ ] ServiceMonitor виден в Prometheus targets\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "helm template habitflow helm/habitflow | kube-score score -\n"
                            "# Все backend ресурсы должны получить CRITICAL: 0\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                    {
                        "type": "Task",
                        "summary": "Frontend Deployment, Ingress TLS (cert-manager), Backup CronJob",
                        "description": (
                            "## Описание\n"
                            "- `templates/frontend/deployment.yaml`, `service.yaml`, `configmap-nginx.yaml`\n"
                            "- `templates/ingress.yaml`: TLS с аннотацией cert-manager, hostname из values\n"
                            "- `templates/cronjob-backup.yaml`: `0 3 * * *`, `pg_dump` → PVC, "
                            "ротация (оставить 7 последних через `ls -t | tail -n +8 | xargs rm`)\n"
                            "- PVC для backup (2Gi), `templates/secrets.yaml` (template с комментарием)\n"
                            "- Runbook: как настроить cert-manager ClusterIssuer (selfsigned)\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Ingress доступен по `habitflow.local` с TLS\n"
                            "- [ ] Backup CronJob создаёт `.sql.gz` файл в PVC\n"
                            "- [ ] После 8 бэкапов: старый удаляется (максимум 7)\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "kubectl create job --from=cronjob/habitflow-backup manual-test -n habitflow\n"
                            "kubectl wait --for=condition=complete job/manual-test -n habitflow --timeout=120s\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                    {
                        "type": "Task",
                        "summary": "Deploy в K3s и smoke test",
                        "description": (
                            "## Описание\n"
                            "Выполнить первый деплой в K3s согласно Appendix B из ТЗ:\n"
                            "1. `kubectl create namespace habitflow`\n"
                            "2. Создать secret habitflow-secrets\n"
                            "3. `helm dependency update && helm install habitflow`\n"
                            "4. Дождаться ready всех подов\n"
                            "5. Зайти на https://habitflow.local, зарегистрироваться, создать привычку, отметить\n"
                            "6. Проверить метрики в Grafana, логи в Loki\n"
                            "7. Выполнить rolling update (bump image tag)\n"
                            "8. Выполнить helm rollback — убедиться что работает\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer / 🏗️ SRE\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все поды Running\n"
                            "- [ ] Приложение доступно по https://habitflow.local\n"
                            "- [ ] Rolling update без downtime\n"
                            "- [ ] Helm rollback возвращает предыдущую версию\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "kubectl get pods -n habitflow | grep -v Running && exit 1 || echo 'All pods Running'\n"
                            "curl -sk https://habitflow.local/healthz | jq .status\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 6,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 10: CI/CD Pipeline
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[CICD] CI/CD Pipeline & Security Scanning",
        "description": (
            "GitHub Actions: lint, test, build, push images, helm validate, security scan, release workflow.\n\n"
            "**Фаза:** Phase 4\n"
            "**Требования:** ТЗ §13.5"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "CI Pipeline (lint, test, build, security)",
                "description": "ci.yml со всеми jobs, кэшированием, артефактами и coverage gates.",
                "sprint": 5,
                "children": [
                    {
                        "type": "Task",
                        "summary": "ci.yml: backend lint, test с coverage gate ≥80%",
                        "description": (
                            "## Описание\n"
                            "Создать `.github/workflows/ci.yml` jobs:\n"
                            "**backend-lint:** `golangci-lint run` с конфигом `.golangci.yml` (включить: errcheck, govet, staticcheck)\n"
                            "**backend-test:**\n"
                            "- `go test ./... -race -coverprofile=coverage.out`\n"
                            "- Upload coverage artifact\n"
                            "- Coverage gate: если `go tool cover -func | grep total` < 80% → fail\n"
                            "- `go build ./...` — проверка компиляции\n"
                            "- Кэш: `~/.cache/go-build` и `~/go/pkg/mod`\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] lint job падает при новом lint warning\n"
                            "- [ ] Coverage < 80% → CI fail\n"
                            "- [ ] Повторный run: кэш экономит ≥ 50% времени\n\n"
                            "## Автоматизированная проверка\n"
                            "GitHub Actions run log: проверить что все jobs зелёные."
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                    {
                        "type": "Task",
                        "summary": "ci.yml: frontend test, helm validate, security scan (gosec, trivy)",
                        "description": (
                            "## Описание\n"
                            "Добавить jobs в ci.yml:\n"
                            "**frontend-test:** `eslint + tsc --noEmit + vitest run --coverage` (gate ≥70%)\n"
                            "**helm-validate:** `helm lint + helm template | kubeval + helm template | kube-score`\n"
                            "**security-scan:**\n"
                            "- `gosec ./...` — Go SAST, fail при HIGH\n"
                            "- `trivy image --severity HIGH,CRITICAL` для backend и frontend образов\n"
                            "- `grype` SBOM сканирование\n"
                            "- Upload SARIF report как artifact\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] helm-validate проходит без ошибок\n"
                            "- [ ] trivy: нет CRITICAL уязвимостей в финальных образах\n"
                            "- [ ] gosec: нет HIGH severity findings\n\n"
                            "## Автоматизированная проверка\n"
                            "Запуск на чистой ветке: все jobs зелёные."
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                    {
                        "type": "Task",
                        "summary": "release.yml: build + push images + helm diff",
                        "description": (
                            "## Описание\n"
                            "Создать `.github/workflows/release.yml`:\n"
                            "- Trigger: push тега `v*.*.*`\n"
                            "- Build backend и frontend images с тегами: `vX.Y.Z`, `latest`\n"
                            "- Push в `ghcr.io/smirnofflab/habitflow-{backend,frontend}:TAG`\n"
                            "- Настроить Docker layer cache через ghcr.io\n"
                            "- `helm diff upgrade` (требует kubeconfig секрет) — показать что изменится\n"
                            "- Create GitHub Release с changelog (из git log --oneline)\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Push тега v1.0.0 → образы появляются в ghcr.io\n"
                            "- [ ] GitHub Release создаётся автоматически\n"
                            "- [ ] Docker layer cache работает (2-й build на ~70% быстрее)\n\n"
                            "## Автоматизированная проверка\n"
                            "Тег v0.0.1-test → проверить ghcr.io что образы появились."
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 5,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 11: Testing & QA
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[QA] Testing Strategy & E2E",
        "description": (
            "Тест-инфраструктура, unit/integration/E2E тесты, coverage gates, Playwright на мобиле.\n\n"
            "**Фаза:** Все фазы (параллельно с разработкой)\n"
            "**Требования:** ТЗ §13"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "Test Infrastructure Setup",
                "description": "testcontainers-go, фикстуры, Playwright config, coverage gates.",
                "sprint": 2,
                "children": [
                    {
                        "type": "Task",
                        "summary": "Настроить testcontainers-go для integration тестов",
                        "description": (
                            "## Описание\n"
                            "Настроить тестовое окружение для backend integration тестов:\n"
                            "- `testcontainers-go` с PostgreSQL 16 контейнером\n"
                            "- `TestMain`: поднять контейнер → применить миграции → запустить тесты → остановить\n"
                            "- Фабрика тестовых фикстур в `internal/testutil/fixtures.go`:\n"
                            "  `CreateUser(t, db, ...overrides)`, `CreateHabit(t, db, userID, ...overrides)`, "
                            "`CreateEntry(t, db, habitID, date, ...overrides)`\n"
                            "- Helper `WithAuthToken(t, userID)` для authenticated HTTP requests\n\n"
                            "## Исполнитель\n🧪 QA Engineer / 💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `go test ./... -tags=integration` запускается без ручного поднятия БД\n"
                            "- [ ] Тесты изолированы (каждый тест в своей транзакции или очищает данные)\n"
                            "- [ ] Fixtures factory упрощает создание тестовых данных до 1 строки\n\n"
                            "## Автоматизированная проверка\n"
                            "```go\n"
                            "func TestIntegration(t *testing.T) {\n"
                            "    user := fixtures.CreateUser(t, db)\n"
                            "    habit := fixtures.CreateHabit(t, db, user.ID, fixtures.WithType('numeric'))\n"
                            "    assert.NotNil(t, habit.ID)\n"
                            "}\n"
                            "```"
                        ),
                        "expert": "QA Engineer / Backend Developer",
                        "sprint": 2,
                    },
                    {
                        "type": "Task",
                        "summary": "Настроить Playwright E2E с мобильным viewport",
                        "description": (
                            "## Описание\n"
                            "Настроить Playwright в `e2e/` директории:\n"
                            "- `playwright.config.ts`: projects: desktop (chromium 1280×720) + mobile (iPhone 14, 390×844)\n"
                            "- `e2e/fixtures/`: `login(page, username, password)`, `createHabit(page, payload)`, "
                            "`markHabit(page, habitName)`\n"
                            "- `e2e/utils/api.ts`: helper для прямых API вызовов в beforeEach (создание тестовых данных)\n"
                            "- Конфиг: baseURL из ENV, trace on first-retry, screenshot on failure\n"
                            "- CI: `npx playwright install --with-deps` в GitHub Actions\n\n"
                            "## Исполнитель\n🧪 QA Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `npx playwright test` запускается в обоих viewports\n"
                            "- [ ] Скриншоты при падении доступны как CI artifacts\n"
                            "- [ ] Traces записываются для отладки\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "npx playwright test e2e/smoke.spec.ts --reporter=list\n"
                            "```"
                        ),
                        "expert": "QA Engineer",
                        "sprint": 2,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "E2E Test Scenarios (Playwright)",
                "description": "Полный набор E2E сценариев: auth, board, habits, stats, mobile.",
                "sprint": 6,
                "children": [
                    {
                        "type": "Task",
                        "summary": "E2E: auth.spec.ts — регистрация, логин, recovery",
                        "description": (
                            "## Описание\n"
                            "Написать `e2e/auth.spec.ts`:\n"
                            "- `register → save recovery codes → logout → login with recovery code → forced password change`\n"
                            "- `login with wrong password → error message`\n"
                            "- `6 failed logins → rate limit message`\n"
                            "- `access protected route without token → redirect to /login`\n"
                            "- `logout → token cleared → GET /me → 401`\n"
                            "Запускать в обоих viewports (desktop + iPhone 14).\n\n"
                            "## Исполнитель\n🧪 QA Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все 5 сценариев проходят\n"
                            "- [ ] Тесты работают в desktop и mobile viewport\n"
                            "- [ ] Время выполнения < 60 секунд\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "npx playwright test e2e/auth.spec.ts --project=desktop --project=mobile\n"
                            "```"
                        ),
                        "expert": "QA Engineer",
                        "sprint": 6,
                    },
                    {
                        "type": "Task",
                        "summary": "E2E: board.spec.ts + habits.spec.ts + mobile.spec.ts",
                        "description": (
                            "## Описание\n"
                            "**board.spec.ts:**\n"
                            "- Отметить boolean → иконка заполняется\n"
                            "- Ввести numeric 15/20 → не completed; 20/20 → completed\n"
                            "- Навигация на вчера → is_editable\n"
                            "- Навигация на 3 дня назад → 🔒 индикатор, кнопки disabled\n\n"
                            "**habits.spec.ts:**\n"
                            "- Создать все 3 типа привычек\n"
                            "- Архивировать → исчезает из доски\n"
                            "- Drag & drop: перетащить привычку 3 на позицию 1 → reload → проверить порядок\n\n"
                            "**mobile.spec.ts (iPhone 14):**\n"
                            "- Bottom navigation виден и работает\n"
                            "- Swipe влево меняет дату\n"
                            "- Numeric keyboard открывается для numeric input\n\n"
                            "## Исполнитель\n🧪 QA Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Все сценарии проходят\n"
                            "- [ ] mobile.spec.ts на viewport 390×844\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "npx playwright test e2e/{board,habits,mobile}.spec.ts\n"
                            "```"
                        ),
                        "expert": "QA Engineer",
                        "sprint": 6,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # EPIC 12: PWA, Mobile UX & Documentation
    # =========================================================================
    {
        "type": "Epic",
        "summary": "[PWA] PWA, Mobile Polish & Documentation",
        "description": (
            "PWA установка на iOS, bottom navigation, accessibility, i18n, документация.\n\n"
            "**Фаза:** Phase 5\n"
            "**Требования:** ТЗ §8.4, §8.5, §3.2"
        ),
        "sprint": None,
        "children": [
            {
                "type": "Story",
                "summary": "PWA & Mobile UX Polish",
                "description": "Service worker, Bottom Navigation, 44pt tap targets, WCAG 2.1 AA аудит.",
                "sprint": 6,
                "children": [
                    {
                        "type": "Task",
                        "summary": "PWA: service worker, manifest, иконки",
                        "description": (
                            "## Описание\n"
                            "Финализировать PWA конфигурацию:\n"
                            "- Service worker (Workbox через Vite PWA): cache-first для статики, network-first для `/api/`\n"
                            "- Offline fallback: если `/api/` недоступен → 'Нет соединения' страница\n"
                            "- Manifest: name, short_name, theme_color, background_color, display, start_url, orientation\n"
                            "- Иконки: 192px, 512px, maskable 512px (создать из SVG логотипа)\n"
                            "- Протестировать 'Add to Home Screen' на реальном iPhone\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Lighthouse PWA: 100/100\n"
                            "- [ ] Устанавливается на iPhone без предупреждений\n"
                            "- [ ] Запускается без адресной строки (standalone)\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "# Lighthouse CI\n"
                            "npx lhci autorun --collect.url=https://habitflow.local\n"
                            "# Lighthouse PWA score должен быть 100\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 6,
                    },
                    {
                        "type": "Task",
                        "summary": "Bottom Navigation + safe-area-inset + mobile touch UX",
                        "description": (
                            "## Описание\n"
                            "**Bottom Navigation (мобиль < 768px):**\n"
                            "- Фиксированный tab bar внизу: Сегодня / Статистика / Привычки / Настройки\n"
                            "- `padding-bottom: env(safe-area-inset-bottom)` для iPhone с Home Indicator\n"
                            "- Активная вкладка: заполненная иконка + акцент-цвет\n"
                            "- Анимация: иконка scale 1→1.1 при нажатии (50ms)\n"
                            "**Mobile touch improvements:**\n"
                            "- Все интерактивные элементы ≥ 44×44pt (проверить через Axe DevTools)\n"
                            "- `inputmode='numeric'` / `inputmode='decimal'` на числовых полях\n"
                            "- Убрать горизонтальный scroll на 320px viewport\n"
                            "- Disabled zoom на iOS: `<meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1'>`\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] Bottom Navigation работает на iPhone (real device)\n"
                            "- [ ] safe-area-inset учтён — контент не скрыт под Home Indicator\n"
                            "- [ ] Нет горизонтального скролла на 320px\n"
                            "- [ ] Все touch targets ≥ 44×44pt (Axe DevTools не показывает ошибок)\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "# Playwright на mobile viewport\n"
                            "npx playwright test mobile.spec.ts --project=mobile\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 6,
                    },
                    {
                        "type": "Task",
                        "summary": "WCAG 2.1 AA Accessibility Audit + тёмная/светлая тема",
                        "description": (
                            "## Описание\n"
                            "**Accessibility audit:**\n"
                            "- Запустить axe-core на всех страницах, устранить все CRITICAL и SERIOUS нарушения\n"
                            "- Контраст текста ≥ 4.5:1 (AA) на обеих темах\n"
                            "- Все формы: `<label for>` или `aria-label`\n"
                            "- Keyboard navigation: Tab/Shift+Tab/Enter/Space работает без мыши\n"
                            "- Focus ring виден на всех интерактивных элементах (не `outline: none`)\n"
                            "- Screen reader: кнопки имеют `aria-label`, состояния — `aria-pressed`/`aria-checked`\n"
                            "**Тема light/dark:**\n"
                            "- `prefers-color-scheme: dark` определяет тему по умолчанию ('system')\n"
                            "- Переключение через class `dark` на `<html>`, без flash при загрузке\n"
                            "- Цвета из ТЗ §8.1 реализованы через CSS переменные\n\n"
                            "## Исполнитель\n🎨 Frontend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `npx axe http://localhost:3000` — 0 критических нарушений\n"
                            "- [ ] Полная навигация клавиатурой через все 4 экрана\n"
                            "- [ ] Контраст ≥ 4.5:1 в обеих темах (проверить через Colour Contrast Analyser)\n"
                            "- [ ] VoiceOver iOS: можно войти и отметить привычку\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "npx axe-cli http://localhost:3000 --exit\n"
                            "npx axe-cli http://localhost:3000/habits --exit\n"
                            "# Оба должны завершиться с кодом 0\n"
                            "```"
                        ),
                        "expert": "Frontend Developer",
                        "sprint": 7,
                    },
                ],
            },
            {
                "type": "Story",
                "summary": "Documentation & Final Polish",
                "description": "README, runbook, OpenAPI YAML, seed скрипт, финальный smoke test.",
                "sprint": 7,
                "children": [
                    {
                        "type": "Task",
                        "summary": "README.md — полная документация проекта",
                        "description": (
                            "## Описание\n"
                            "Написать итоговый `README.md` в корне репозитория:\n"
                            "- Badges: CI status, License, Docker image size\n"
                            "- **What is HabitFlow** — 2-3 предложения + скриншоты (light + dark theme)\n"
                            "- **Features** — key features из ТЗ §1.4\n"
                            "- **Quick Start (docker-compose)** — 4 команды до работающего приложения\n"
                            "- **Kubernetes Deploy** — ссылка на Appendix B\n"
                            "- **Architecture** — диаграмма из ТЗ §4.1 (ASCII)\n"
                            "- **Development** — make targets, local setup\n"
                            "- **Tech Stack** — таблица из ТЗ §5\n"
                            "- **Contributing** — code style, PR checklist\n"
                            "- **License** — MIT\n\n"
                            "## Исполнитель\n🎯 Tech Lead\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] README рендерится корректно на GitHub (проверить через github.com)\n"
                            "- [ ] Quick Start: новый разработчик может запустить приложение за < 5 мин\n"
                            "- [ ] Все ссылки рабочие\n"
                            "- [ ] Скриншоты обеих тем в `/docs/screenshots/`\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "# Проверка broken links\n"
                            "npx markdown-link-check README.md\n"
                            "```"
                        ),
                        "expert": "Tech Lead",
                        "sprint": 7,
                    },
                    {
                        "type": "Task",
                        "summary": "runbook.md + OpenAPI YAML (docs/api.yaml)",
                        "description": (
                            "## Описание\n"
                            "**docs/runbook.md** — операционные процедуры по Appendix C из ТЗ:\n"
                            "- Ручной бэкап, просмотр логов, подключение к БД, сброс пароля\n"
                            "- Troubleshooting: pod не стартует, БД недоступна, cert-manager ошибка\n"
                            "- Upgrade процедура (helm upgrade → verify → rollback если нужно)\n"
                            "- Восстановление из бэкапа (pg_restore)\n\n"
                            "**docs/api.yaml** — OpenAPI 3.1 спецификация:\n"
                            "- Все эндпоинты из ТЗ §7.2 с request/response схемами\n"
                            "- Генерировать через `swaggo/swag` из комментариев к handlers\n"
                            "- Swagger UI доступен на `/api/v1/swagger/index.html` в dev режиме\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer / 💻 Backend Developer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `swagger-cli validate docs/api.yaml` — 0 ошибок\n"
                            "- [ ] Swagger UI доступен и все эндпоинты имеют примеры\n"
                            "- [ ] runbook содержит все операции из Appendix C\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "npx @apidevtools/swagger-cli validate docs/api.yaml && echo 'OpenAPI OK'\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer / Backend Developer",
                        "sprint": 7,
                    },
                    {
                        "type": "Task",
                        "summary": "seed-db.sh + setup-dev.sh + финальный smoke test",
                        "description": (
                            "## Описание\n"
                            "**scripts/seed-db.sh:**\n"
                            "- Создать тестового пользователя `demo / Demo1234!`\n"
                            "- Создать 5 привычек (boolean, numeric×2, duration×2) с разными категориями\n"
                            "- Заполнить entries за последние 30 дней (~80% completion rate)\n"
                            "- Используется для демо и E2E тестов\n\n"
                            "**scripts/setup-dev.sh:**\n"
                            "- Проверить наличие Docker, Node 22, Go 1.23, kubectl, helm\n"
                            "- Запустить generate-keys.sh если ключи отсутствуют\n"
                            "- Создать `.env.local` из `.env.local.example`\n"
                            "- `docker-compose up -d && sleep 10 && make seed`\n\n"
                            "**Финальный smoke test (CI job 'smoke'):**\n"
                            "- docker-compose up → seed → Playwright smoke suite (5 критических сценариев)\n"
                            "- Время: < 3 минуты\n\n"
                            "## Исполнитель\n🔧 DevOps Engineer\n\n"
                            "## Критерии приёмки\n"
                            "- [ ] `bash scripts/setup-dev.sh` на чистой машине: приложение работает\n"
                            "- [ ] Seed данные видны в Grafana Business dashboard\n"
                            "- [ ] Smoke test в CI проходит за < 3 мин\n\n"
                            "## Автоматизированная проверка\n"
                            "```bash\n"
                            "bash scripts/setup-dev.sh 2>&1 | tail -5\n"
                            "curl -sf http://localhost:8080/healthz && echo 'Smoke OK'\n"
                            "```"
                        ),
                        "expert": "DevOps Engineer",
                        "sprint": 7,
                    },
                ],
            },
        ],
    },
]

# =============================================================================
# JIRA API CLIENT
# =============================================================================

try:
    import requests
    from requests.auth import HTTPBasicAuth
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.parse


class JiraClient:
    """Тонкая обёртка над Jira Cloud REST API v2 + Agile API."""

    def __init__(self, base_url: str, email: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.token = token
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.auth = HTTPBasicAuth(email, token)
            self.session.headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
        else:
            import base64
            creds = base64.b64encode(f"{email}:{token}".encode()).decode()
            self._auth_header = f"Basic {creds}"

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        if HAS_REQUESTS:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        else:
            req = urllib.request.Request(url, headers={
                "Authorization": self._auth_header,
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())

    def _post(self, path: str, data: dict) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode()
        if HAS_REQUESTS:
            resp = self.session.post(url, json=data, timeout=30)
            if resp.status_code not in (200, 201):
                log.error("POST %s → %s: %s", path, resp.status_code, resp.text[:500])
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        else:
            req = urllib.request.Request(url, data=body, method="POST", headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode()) if r.length else {}

    def _put(self, path: str, data: dict) -> None:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode()
        if HAS_REQUESTS:
            resp = self.session.put(url, json=data, timeout=30)
            if resp.status_code not in (200, 201, 204):
                log.error("PUT %s → %s: %s", path, resp.status_code, resp.text[:500])
            resp.raise_for_status()
        else:
            req = urllib.request.Request(url, data=body, method="PUT", headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
            })
            urllib.request.urlopen(req, timeout=30)

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    def create_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str,
        parent_key: Optional[str] = None,
        epic_key: Optional[str] = None,
        sprint_id: Optional[int] = None,
        epic_name: Optional[str] = None,
        custom_fields: Optional[dict] = None,
    ) -> str:
        """Создать задачу в Jira. Вернуть ключ созданного тикета (например, HF-42)."""
        fields: dict = {
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary[:255],  # Jira ограничение
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
        }

        # Epic Name для Epics (Jira Cloud требует это поле)
        if issue_type == "Epic" and epic_name:
            fields["customfield_10011"] = epic_name  # Epic Name

        # Parent (Story → Epic, Task → Story)
        if parent_key:
            if issue_type == "Story":
                # В Jira Cloud story → epic через parent
                fields["parent"] = {"key": parent_key}
            elif issue_type == "Task":
                fields["parent"] = {"key": parent_key}

        # Epic Link (если используется старый API)
        if epic_key and issue_type in ("Story", "Task"):
            fields["customfield_10014"] = epic_key  # Epic Link

        # Sprint
        if sprint_id is not None:
            fields["customfield_10020"] = sprint_id

        # Дополнительные поля
        if custom_fields:
            fields.update(custom_fields)

        result = self._post("/rest/api/3/issue", {"fields": fields})
        key = result.get("key", "")
        log.info("  ✅ Created %s [%s]: %s", issue_type, key, summary[:60])
        return key

    # ------------------------------------------------------------------
    # Sprints (Agile API)
    # ------------------------------------------------------------------

    def get_board_id(self, project_key: str) -> Optional[int]:
        """Получить ID первой Scrum-доски проекта."""
        try:
            data = self._get(f"/rest/agile/1.0/board?projectKeyOrId={project_key}&type=scrum")
            values = data.get("values", [])
            if values:
                return values[0]["id"]
        except Exception as exc:
            log.warning("Не удалось получить board_id: %s", exc)
        return None

    def get_sprints(self, board_id: int) -> list:
        """Получить все спринты доски."""
        try:
            data = self._get(f"/rest/agile/1.0/board/{board_id}/sprint?state=active,future,closed")
            return data.get("values", [])
        except Exception as exc:
            log.warning("Не удалось получить спринты: %s", exc)
            return []

    def get_or_create_sprint(
        self, board_id: int, sprint_number: int, project_key: str
    ) -> Optional[int]:
        """Найти спринт с номером sprint_number или создать его."""
        sprint_name = f"Sprint {sprint_number}"
        sprints = self.get_sprints(board_id)
        for sp in sprints:
            if sp.get("name", "").strip() == sprint_name:
                log.debug("  Sprint найден: %s (id=%s)", sprint_name, sp["id"])
                return sp["id"]

        # Создать новый спринт
        try:
            result = self._post("/rest/agile/1.0/sprint", {
                "name": sprint_name,
                "originBoardId": board_id,
            })
            sprint_id = result.get("id")
            log.info("  📅 Создан спринт: %s (id=%s)", sprint_name, sprint_id)
            return sprint_id
        except Exception as exc:
            log.warning("Не удалось создать спринт %s: %s", sprint_name, exc)
            return None

    def move_to_sprint(self, sprint_id: int, issue_keys: list) -> None:
        """Переместить задачи в спринт."""
        if not issue_keys:
            return
        try:
            self._post(f"/rest/agile/1.0/sprint/{sprint_id}/issue", {
                "issues": issue_keys,
            })
        except Exception as exc:
            log.warning("Не удалось переместить %s в спринт %s: %s", issue_keys, sprint_id, exc)


# =============================================================================
# ИЕРАРХИЧЕСКОЕ СОЗДАНИЕ ТИКЕТОВ
# =============================================================================

class IssueCreator:
    """Обходит иерархию ISSUES и создаёт тикеты в Jira."""

    def __init__(
        self,
        client: JiraClient,
        project_key: str,
        board_id: Optional[int],
        dry_run: bool = False,
    ):
        self.client = client
        self.project_key = project_key
        self.board_id = board_id
        self.dry_run = dry_run

        # Кэш спринтов: номер → id
        self._sprint_cache: dict[int, int] = {}

        # Статистика
        self.stats = {"created": 0, "skipped": 0, "errors": 0}

    def _get_sprint_id(self, sprint_number: Optional[int]) -> Optional[int]:
        if sprint_number is None or self.board_id is None:
            return None
        if sprint_number not in self._sprint_cache:
            sid = self.client.get_or_create_sprint(
                self.board_id, sprint_number, self.project_key
            )
            if sid:
                self._sprint_cache[sprint_number] = sid
        return self._sprint_cache.get(sprint_number)

    def create_all(self) -> None:
        log.info("🚀 Начало создания тикетов в проекте %s", self.project_key)
        log.info("   Режим: %s", "DRY-RUN (тикеты не создаются)" if self.dry_run else "LIVE")
        log.info("   Всего эпиков: %d", len(ISSUES))

        for epic_data in ISSUES:
            self._process_epic(epic_data)

        log.info(
            "\n📊 Итого: ✅ создано=%d  ⏩ пропущено=%d  ❌ ошибок=%d",
            self.stats["created"],
            self.stats["skipped"],
            self.stats["errors"],
        )

    def _process_epic(self, epic_data: dict) -> None:
        summary = epic_data["summary"]
        log.info("\n📦 EPIC: %s", summary)

        if self.dry_run:
            self.stats["skipped"] += 1
            epic_key = f"{self.project_key}-DRY"
        else:
            try:
                epic_key = self.client.create_issue(
                    project_key=self.project_key,
                    issue_type="Epic",
                    summary=summary,
                    description=epic_data.get("description", ""),
                    epic_name=re.sub(r"^\[.*?\]\s*", "", summary),  # без [PREFIX]
                )
                self.stats["created"] += 1
            except Exception as exc:
                log.error("❌ Ошибка создания Epic '%s': %s", summary, exc)
                self.stats["errors"] += 1
                return

        time.sleep(0.3)

        for story_data in epic_data.get("children", []):
            self._process_story(story_data, epic_key)

    def _process_story(self, story_data: dict, epic_key: str) -> None:
        summary = story_data["summary"]
        sprint_number = story_data.get("sprint")
        sprint_id = self._get_sprint_id(sprint_number)

        log.info("  📖 Story: %s (Sprint %s)", summary, sprint_number)

        if self.dry_run:
            self.stats["skipped"] += 1
            story_key = f"{self.project_key}-DRY"
        else:
            try:
                story_key = self.client.create_issue(
                    project_key=self.project_key,
                    issue_type="Story",
                    summary=summary,
                    description=story_data.get("description", ""),
                    parent_key=epic_key,
                    epic_key=epic_key,
                    sprint_id=sprint_id,
                )
                self.stats["created"] += 1
            except Exception as exc:
                log.error("❌ Ошибка создания Story '%s': %s", summary, exc)
                self.stats["errors"] += 1
                return

        time.sleep(0.3)

        for task_data in story_data.get("children", []):
            self._process_task(task_data, story_key, epic_key)

    def _process_task(self, task_data: dict, story_key: str, epic_key: str) -> None:
        summary = task_data["summary"]
        sprint_number = task_data.get("sprint")
        sprint_id = self._get_sprint_id(sprint_number)

        log.info("     🔧 Task: %s (Sprint %s)", summary, sprint_number)

        if self.dry_run:
            self.stats["skipped"] += 1
            return

        try:
            self.client.create_issue(
                project_key=self.project_key,
                issue_type="Task",
                summary=summary,
                description=task_data.get("description", ""),
                parent_key=story_key,
                epic_key=epic_key,
                sprint_id=sprint_id,
            )
            self.stats["created"] += 1
        except Exception as exc:
            log.error("❌ Ошибка создания Task '%s': %s", summary, exc)
            self.stats["errors"] += 1

        time.sleep(0.3)


# =============================================================================
# ENTRYPOINT
# =============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HabitFlow — автоматическое создание иерархии тикетов в Jira",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Dry-run: только показать что будет создано
  python3 HabitFlow.py --project HF --email you@example.com --token TOKEN --dry-run

  # Создать все тикеты
  python3 HabitFlow.py --project HF --email you@example.com --token TOKEN

  # Указать свой Jira URL (Server/Data Center)
  python3 HabitFlow.py --project HF --email admin --token TOKEN \\
      --jira-url https://jira.company.intranet

  # Создать только конкретный эпик (по индексу 0-based)
  python3 HabitFlow.py --project HF --email you@example.com --token TOKEN --epic 0

Получить API-токен:
  Jira Cloud: https://id.atlassian.com/manage-profile/security/api-tokens
  Jira Server: Profile → Personal Access Tokens
        """,
    )
    parser.add_argument("--project", required=not ("--list" in sys.argv), help="Ключ проекта в Jira (например, HF)")
    parser.add_argument("--email", required=not ("--list" in sys.argv), help="Email аккаунта Jira")
    parser.add_argument("--token", required=not ("--list" in sys.argv), help="API токен Jira")
    parser.add_argument(
        "--jira-url",
        default="https://your-domain.atlassian.net",
        help="Базовый URL Jira (default: https://your-domain.atlassian.net)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Не создавать тикеты, только показать иерархию",
    )
    parser.add_argument(
        "--epic",
        type=int,
        default=None,
        metavar="INDEX",
        help="Создать только один эпик по индексу (0-based). По умолчанию — все.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        metavar="SEC",
        help="Задержка между запросами в секундах (default: 0.3)",
    )
    parser.add_argument(
        "--no-sprints",
        action="store_true",
        help="Не создавать/назначать спринты (полезно если доска Kanban)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Вывести список всех эпиков и задач без создания",
    )
    return parser.parse_args()


def list_issues() -> None:
    """Вывести полную иерархию тикетов в консоль (без Jira)."""
    total_epics = len(ISSUES)
    total_stories = sum(len(e.get("children", [])) for e in ISSUES)
    total_tasks = sum(
        len(s.get("children", []))
        for e in ISSUES
        for s in e.get("children", [])
    )
    print(f"\nHabitFlow — Иерархия тикетов")
    print(f"{'='*60}")
    print(f"Эпиков: {total_epics}  |  Сторей: {total_stories}  |  Задач: {total_tasks}")
    print(f"{'='*60}\n")

    for i, epic in enumerate(ISSUES):
        sprint_info = f"Sprint {epic['sprint']}" if epic.get("sprint") else "—"
        print(f"[{i:02d}] 📦 EPIC: {epic['summary']}")
        for story in epic.get("children", []):
            sp = f"Sprint {story.get('sprint', '?')}"
            print(f"       📖 Story [{sp}]: {story['summary']}")
            for task in story.get("children", []):
                sp_t = f"Sprint {task.get('sprint', '?')}"
                expert = task.get("expert", "—")
                print(f"            🔧 [{sp_t}] {task['summary']}")
                print(f"               👤 {expert}")
    print()


def main() -> int:
    args = parse_args()

    # Просто показать список
    if args.list:
        list_issues()
        return 0

    # Проверить зависимости
    if not HAS_REQUESTS:
        log.warning(
            "Библиотека 'requests' не установлена. Используется urllib (ограниченная функциональность).\n"
            "Рекомендуется: pip install requests"
        )

    # Создать клиент
    client = JiraClient(
        base_url=args.jira_url,
        email=args.email,
        token=args.token,
    )

    # Проверить подключение
    log.info("🔌 Подключение к Jira: %s", args.jira_url)
    try:
        me = client._get("/rest/api/3/myself")
        log.info("   Аутентифицирован как: %s (%s)", me.get("displayName"), me.get("emailAddress"))
    except Exception as exc:
        log.error("❌ Не удалось подключиться к Jira: %s", exc)
        log.error("   Проверьте: --jira-url, --email, --token")
        return 1

    # Получить board ID для спринтов
    board_id: Optional[int] = None
    if not args.no_sprints:
        board_id = client.get_board_id(args.project)
        if board_id:
            log.info("   Board ID: %d", board_id)
        else:
            log.warning("   Scrum-доска не найдена. Спринты не будут назначены.")

    # Фильтр по эпику
    issues_to_process = ISSUES
    if args.epic is not None:
        if args.epic < 0 or args.epic >= len(ISSUES):
            log.error("❌ Индекс --epic=%d выходит за диапазон 0–%d", args.epic, len(ISSUES) - 1)
            return 1
        issues_to_process = [ISSUES[args.epic]]
        log.info("   Создаём только эпик #%d: %s", args.epic, issues_to_process[0]["summary"])

    # Запустить создание
    creator = IssueCreator(
        client=client,
        project_key=args.project,
        board_id=board_id,
        dry_run=args.dry_run,
    )
    # Применить delay из args
    import builtins
    _orig_sleep = time.sleep
    time.sleep = lambda s: _orig_sleep(args.delay)

    # Ограничить до выбранных эпиков
    _original_issues = ISSUES.copy()
    ISSUES.clear()
    ISSUES.extend(issues_to_process)
    try:
        creator.create_all()
    finally:
        ISSUES.clear()
        ISSUES.extend(_original_issues)
        time.sleep = _orig_sleep

    return 0 if creator.stats["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())