# HabitFlow — Техническое задание
### Персональный трекер привычек для self-hosted Kubernetes (K3s)

**Версия:** 1.0  
**Дата:** 2026-06-21  
**Статус:** Draft

---

## Содержание

1. [Обзор проекта](#1-обзор-проекта)
2. [Функциональные требования](#2-функциональные-требования)
3. [Нефункциональные требования](#3-нефункциональные-требования)
4. [Архитектура системы](#4-архитектура-системы)
5. [Технический стек](#5-технический-стек)
6. [Схема базы данных](#6-схема-базы-данных)
7. [REST API](#7-rest-api)
8. [Frontend — UI/UX спецификация](#8-frontend--uiux-спецификация)
9. [Аутентификация и безопасность](#9-аутентификация-и-безопасность)
10. [Мониторинг и логирование](#10-мониторинг-и-логирование)
11. [Helm Chart и Kubernetes манифесты](#11-helm-chart-и-kubernetes-манифесты)
12. [Структура репозитория](#12-структура-репозитория)
13. [Стратегия тестирования](#13-стратегия-тестирования)
14. [Фазы разработки и MVP](#14-фазы-разработки-и-mvp)
15. [Открытые вопросы и решения](#15-открытые-вопросы-и-решения)

---

## 1. Обзор проекта

### 1.1 Назначение

HabitFlow — это self-hosted веб-приложение для ежедневного трекинга привычек. Устанавливается в Kubernetes (K3s) и доступно из домашней сети, в том числе через VPN. Не требует внешних интеграций и полностью контролируется пользователем.

### 1.2 Целевая аудитория

Один или несколько пользователей в домашней/частной сети. Множественные аккаунты поддерживаются, но регистрация не предполагает публичного доступа.

### 1.3 Ключевые концепции

| Понятие | Описание |
|---|---|
| **Привычка (Habit)** | Повторяющееся ежедневное действие с заданными параметрами |
| **Запись (Entry)** | Факт выполнения привычки в конкретный день |
| **Окно редактирования** | Количество дней в прошлое, доступных для правки (по умолчанию: 1) |
| **Стрик (Streak)** | Непрерывная серия выполненных дней |
| **Доска (Board)** | Главный экран — матрица привычек × дни |

### 1.4 Ключевые отличия от готовых решений

- Полностью self-hosted, zero-telemetry
- Нативный Kubernetes deployment с Helm
- Встроенные метрики Prometheus + Grafana dashboards
- Конфигурируемое окно редактирования прошлого
- Поддержка количественных привычек (не только бинарных)

---

## 2. Функциональные требования

### 2.1 Аутентификация

| ID | Требование | Приоритет |
|---|---|---|
| AUTH-01 | Регистрация по логину + пароль | Must |
| AUTH-02 | Вход с выдачей JWT access + refresh token | Must |
| AUTH-03 | Logout с инвалидацией refresh token | Must |
| AUTH-04 | Восстановление доступа через одноразовый recovery code (генерируется при регистрации, хранится у пользователя) | Must |
| AUTH-05 | Смена пароля в профиле | Must |
| AUTH-06 | Возможность принудительного сброса пароля через CLI-команду на поде бэкенда (для администратора) | Should |
| AUTH-07 | Rate limiting на /auth/* эндпоинтах | Must |
| AUTH-08 | Сессии: access token — 15 мин, refresh — 30 дней (конфигурируемо) | Must |

> **Восстановление доступа (AUTH-04):** При регистрации генерируется набор из 8 одноразовых recovery codes (bcrypt-хэши хранятся в БД). Пользователь скачивает/копирует их при создании аккаунта. Один код — один вход, после чего принудительно требуется смена пароля. Без внешнего SMTP.

### 2.2 Управление привычками

| ID | Требование | Приоритет |
|---|---|---|
| HAB-01 | Создание привычки: название, тип, категория, цвет, иконка, описание | Must |
| HAB-02 | Типы привычек: **boolean** (сделал/не сделал), **numeric** (числовое значение + единица + цель), **duration** (минуты) | Must |
| HAB-03 | Архивирование привычки (скрытие из активных без удаления истории) | Must |
| HAB-04 | Удаление привычки с каскадным удалением записей (с подтверждением) | Must |
| HAB-05 | Порядок привычек — перетаскивание (drag & drop) | Should |
| HAB-06 | Категории (теги) с цветовой маркировкой | Should |
| HAB-07 | Частота: ежедневно / конкретные дни недели / X раз в неделю | Should |
| HAB-08 | Целевое значение для numeric-привычек | Must |
| HAB-09 | Описание/заметка к привычке | Could |
| HAB-10 | Импорт/экспорт в JSON | Could |

### 2.3 Трекинг и Доска

| ID | Требование | Приоритет |
|---|---|---|
| TRK-01 | Главная доска: список привычек + кнопки отметки для текущего дня | Must |
| TRK-02 | Отметка Boolean: toggleable кнопка (off → on → off) | Must |
| TRK-03 | Отметка Numeric: inline ввод числа, +/- кнопки | Must |
| TRK-04 | Отметка Duration: ввод минут | Must |
| TRK-05 | Навигация по дням: стрелки назад/вперёд | Must |
| TRK-06 | Конфигурируемое окно редактирования прошлого (edit\_window\_days, default=1) | Must |
| TRK-07 | Дни вне окна редактирования — read-only с визуальным индикатором блокировки | Must |
| TRK-08 | Будущие даты недоступны для отметки | Must |
| TRK-09 | Индикатор прогресса дня (X из N привычек выполнено) | Must |
| TRK-10 | Стрик для каждой привычки (текущий + максимальный) | Must |
| TRK-11 | Месячная матрица (GitHub-style heatmap) в деталях привычки | Should |
| TRK-12 | Заметка к записи дня | Could |
| TRK-13 | Быстрый переход к сегодняшнему дню | Must |

### 2.4 Статистика и Аналитика

| ID | Требование | Приоритет |
|---|---|---|
| STAT-01 | Completion rate за последние 7 / 30 / 90 дней по каждой привычке | Must |
| STAT-02 | Общий прогресс за произвольный период | Should |
| STAT-03 | График выполнения по времени (line chart) | Should |
| STAT-04 | Тепловая карта года (calendar heatmap) | Should |
| STAT-05 | Сравнение привычек по категориям | Could |
| STAT-06 | Лучшие недели/месяцы | Could |

### 2.5 Настройки пользователя

| ID | Требование | Приоритет |
|---|---|---|
| SET-01 | Часовой пояс пользователя | Must |
| SET-02 | Первый день недели (Пн / Вс) | Should |
| SET-03 | Тема: светлая / тёмная / системная | Must |
| SET-04 | Конфигурация edit_window_days (1–30) | Must |
| SET-05 | Язык интерфейса (ru / en) | Should |
| SET-06 | Аватар | Could |

---

## 3. Нефункциональные требования

### 3.1 Производительность

- API ответ на 95 перцентиле: < 200 мс (без холодного старта)
- Главная страница (LCP): < 1.5 сек на мобиле (3G slow)
- База данных: все основные запросы — O(log n) с индексами
- Поддержка до 10 одновременных пользователей (домашняя лаборатория)

### 3.2 Доступность и адаптивность

- Responsive breakpoints: 320px / 768px / 1024px / 1440px
- Touch-friendly на iPhone: минимальный tap target 44×44px
- Без горизонтального скролла на 320px
- WCAG 2.1 AA — минимальный контраст текста

### 3.3 Надёжность

- Graceful degradation при недоступности БД (503 с информативным сообщением)
- Healthcheck эндпоинты для Kubernetes liveness/readiness проб
- Автоматический rollback через Helm при провале health checks
- Резервное копирование PostgreSQL через CronJob (pg_dump → PVC)

### 3.4 Безопасность

- Все пароли — Argon2id
- JWT RS256 (асимметричные ключи)
- HTTPS внутри кластера (cert-manager + self-signed CA) или TLS termination на Ingress
- Content Security Policy (CSP) заголовки
- Не хранить секреты в образах; только через Kubernetes Secrets
- Принцип минимальных прав (RBAC на уровне K8s ServiceAccount)

### 3.5 Поддерживаемость

- Вся конфигурация через Helm values.yaml
- Структурированные JSON-логи во всех компонентах
- Версионирование API (/api/v1/)
- Миграции БД — автоматические при старте (golang-migrate)
- Каждый компонент — отдельный модуль с независимым релизным циклом

---

## 4. Архитектура системы

### 4.1 Общая схема

```
┌──────────────────────────────────────────────────────────────────┐
│                         Kubernetes (K3s)                         │
│  namespace: habitflow                                            │
│                                                                  │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  Ingress    │───▶│    Frontend     │    │   Backend API   │  │
│  │  (Nginx /   │    │  (Nginx, SPA)   │    │   (Go, Echo)    │  │
│  │  Traefik)   │───▶│  :3000          │───▶│   :8080         │  │
│  └─────────────┘    └─────────────────┘    └────────┬────────┘  │
│         ▲                                           │            │
│         │                                  ┌────────▼────────┐  │
│  ┌──────┴──────┐                           │   PostgreSQL    │  │
│  │  VPN / DNS  │                           │   :5432         │  │
│  │  (WireGuard)│                           └─────────────────┘  │
│  └─────────────┘                                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  namespace: monitoring                                   │    │
│  │  Prometheus → Grafana → Loki → Alertmanager             │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Компонент: Frontend

- Статический SPA (Single Page Application)
- Собирается в Docker образ с Nginx для раздачи файлов
- Runtime-конфигурация через `window.__ENV__` (inject при старте контейнера из ConfigMap)
- Взаимодействует исключительно с Backend API через `/api/v1/`
- Nginx проксирует `/api/` на backend Service

### 4.3 Компонент: Backend API

- HTTP-сервер на Go
- Stateless — горизонтально масштабируем (HPA)
- Все состояние — в PostgreSQL
- Refresh tokens хранятся в БД (таблица `sessions`) — поддержка инвалидации
- Метрики Prometheus на `:9090/metrics`
- Healthcheck: `GET /healthz` (liveness), `GET /readyz` (readiness — проверяет соединение с БД)

### 4.4 Компонент: PostgreSQL

- StatefulSet с одной репликой
- Данные на PersistentVolumeClaim (local-path provisioner или NFS)
- Инициализация через init-скрипт (создание ролей, расширений)
- Автоматические миграции — запускает backend при старте
- CronJob для ежедневного pg_dump с ротацией (хранить последние 7 дамп-файлов)

### 4.5 Взаимодействие компонентов

```
Browser / Mobile
      │
      │ HTTPS (443)
      ▼
  Ingress (habitflow.local или habitflow.home)
      │
      ├── /* → Frontend Pod (Nginx)
      │          │
      │          └── /api/* → Backend Service
      │
      └── /api/* → Backend Service
                       │
                       └── Backend Pod
                                │
                                ├── PostgreSQL Service
                                └── /metrics → Prometheus ServiceMonitor
```

---

## 5. Технический стек

### 5.1 Frontend

| Компонент | Выбор | Обоснование |
|---|---|---|
| Язык | TypeScript 5.x | Строгая типизация, стандарт |
| Фреймворк | React 18 | Зрелый, большая экосистема |
| Сборщик | Vite 6 | Быстрый hot reload, tree shaking |
| Стиль | Tailwind CSS 4 | Utility-first, легко адаптировать под мобиль |
| UI компоненты | shadcn/ui + Radix UI | Accessible, headless, полностью кастомизируемый |
| Состояние | Zustand + TanStack Query v5 | Минималистичный state + smart server-state caching |
| Роутинг | TanStack Router | Type-safe, file-based routing |
| Формы | React Hook Form + Zod | Производительность + валидация |
| Даты | date-fns | Лёгкий, tree-shakeable |
| Иконки | Lucide React | Минималистичный, консистентный |
| Графики | Recharts | React-native, простой API |
| Drag & Drop | @dnd-kit/core | Accessible, touch-friendly |
| HTTP клиент | ky (fetch-based) | Лёгкий, TypeScript-first |
| Анимации | Framer Motion (только where needed) | Fluid микроинтеракции |
| Локализация | i18next | ru/en |
| PWA | Vite PWA Plugin | Установка на iPhone, оффлайн-кэш статики |

### 5.2 Backend

| Компонент | Выбор | Обоснование |
|---|---|---|
| Язык | Go 1.23+ | Производительность, малый бинарник, статическая линковка |
| HTTP фреймворк | Echo v4 | Минималистичный, быстрый, хорошая middleware экосистема |
| ORM / Query | sqlc + pgx/v5 | Type-safe SQL без магии ORM, прямой контроль запросов |
| Миграции | golang-migrate | Версионные SQL-миграции в embed |
| JWT | golang-jwt/jwt v5 | RS256 |
| Пароли | alexedwards/argon2id | Argon2id |
| Валидация | go-playground/validator v10 | |
| Конфиг | viper | Env + YAML |
| Логи | zap (uber-go/zap) | Structured JSON logging |
| Метрики | prometheus/client_golang | |
| OpenAPI | swaggo/swag (generate) | Автогенерация из комментариев |
| Тесты | testify + httptest + sqlmock | |

### 5.3 Инфраструктура

| Компонент | Выбор |
|---|---|
| Контейнеризация | Docker (multi-stage build) |
| Оркестрация | Kubernetes K3s |
| Package Manager | Helm v3 |
| Container Registry | ghcr.io или локальный Harbor |
| Ingress | Traefik (встроен в K3s) или Nginx Ingress Controller |
| TLS | cert-manager (self-signed ClusterIssuer) |
| Хранилище секретов | Kubernetes Secrets (в production — интеграция с Vault опционально) |
| Метрики | Prometheus + Grafana |
| Логи | Grafana Alloy (Promtail-совместимый) + Loki |
| CI/CD | GitHub Actions (или Gitea Actions для self-hosted) |
| Резервное копирование | CronJob → pg_dump → PVC |

---

## 6. Схема базы данных

### 6.1 Соглашения

- Все таблицы — snake_case
- Primary keys — `id UUID DEFAULT gen_random_uuid()`
- Timestamps — `TIMESTAMPTZ` (с часовым поясом)
- Soft delete через `deleted_at TIMESTAMPTZ NULL`
- Все FK — с `ON DELETE CASCADE` там, где логически уместно

### 6.2 ERD (Entity Relationship)

```
users
  ├── habits
  │     └── habit_entries
  ├── categories
  ├── sessions
  └── recovery_codes
```

### 6.3 DDL

```sql
-- Расширения
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- для поиска по привычкам

-- ──────────────────────────────────────────
-- Пользователи
-- ──────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,       -- может быть пустым (локальный режим)
    password_hash   VARCHAR(255) NOT NULL,              -- argon2id
    display_name    VARCHAR(100),
    avatar_url      VARCHAR(500),
    timezone        VARCHAR(100) NOT NULL DEFAULT 'Europe/Berlin',
    language        VARCHAR(10)  NOT NULL DEFAULT 'ru',
    week_starts_on  SMALLINT     NOT NULL DEFAULT 1,    -- 0=Sun, 1=Mon
    theme           VARCHAR(20)  NOT NULL DEFAULT 'system', -- light/dark/system
    edit_window_days SMALLINT    NOT NULL DEFAULT 1 CHECK (edit_window_days BETWEEN 1 AND 30),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_email    ON users(email)    WHERE deleted_at IS NULL;

-- ──────────────────────────────────────────
-- Сессии (refresh tokens)
-- ──────────────────────────────────────────
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   VARCHAR(512) NOT NULL UNIQUE, -- bcrypt hash
    user_agent      TEXT,
    ip_address      INET,
    expires_at      TIMESTAMPTZ  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user_id    ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- ──────────────────────────────────────────
-- Recovery codes
-- ──────────────────────────────────────────
CREATE TABLE recovery_codes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash   VARCHAR(255) NOT NULL,  -- bcrypt hash of 8-char code
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recovery_codes_user_id ON recovery_codes(user_id);

-- ──────────────────────────────────────────
-- Категории привычек
-- ──────────────────────────────────────────
CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    color       VARCHAR(7)   NOT NULL DEFAULT '#6366F1', -- hex
    icon        VARCHAR(50),                              -- lucide icon name
    sort_order  SMALLINT     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    UNIQUE(user_id, name)
);

-- ──────────────────────────────────────────
-- Привычки
-- ──────────────────────────────────────────
CREATE TYPE habit_type     AS ENUM ('boolean', 'numeric', 'duration');
CREATE TYPE habit_freq     AS ENUM ('daily', 'weekly', 'custom');

CREATE TABLE habits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     UUID         REFERENCES categories(id) ON DELETE SET NULL,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    type            habit_type   NOT NULL DEFAULT 'boolean',
    frequency       habit_freq   NOT NULL DEFAULT 'daily',
    -- Для weekly/custom
    frequency_days  SMALLINT[]   DEFAULT NULL, -- [1,2,3,4,5] = Пн-Пт
    -- Для numeric
    target_value    NUMERIC(10,2),
    unit            VARCHAR(30),               -- "стакан", "км", "мин"
    -- Визуальное
    color           VARCHAR(7)   NOT NULL DEFAULT '#6366F1',
    icon            VARCHAR(50),
    sort_order      INT          NOT NULL DEFAULT 0,
    is_archived     BOOLEAN      NOT NULL DEFAULT FALSE,
    archived_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_habits_user_id    ON habits(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_habits_category   ON habits(category_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_habits_sort       ON habits(user_id, sort_order) WHERE deleted_at IS NULL;
-- Полнотекстовый поиск
CREATE INDEX idx_habits_name_trgm  ON habits USING gin(name gin_trgm_ops);

-- ──────────────────────────────────────────
-- Записи (факты выполнения)
-- ──────────────────────────────────────────
CREATE TABLE habit_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    habit_id        UUID         NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    user_id         UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date            DATE         NOT NULL,             -- только дата, без времени
    -- boolean: completed = TRUE
    completed       BOOLEAN      NOT NULL DEFAULT FALSE,
    -- numeric / duration
    value           NUMERIC(10,2),
    note            TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(habit_id, date)
);

CREATE INDEX idx_entries_habit_date ON habit_entries(habit_id, date DESC);
CREATE INDEX idx_entries_user_date  ON habit_entries(user_id,  date DESC);
CREATE INDEX idx_entries_date       ON habit_entries(date);

-- ──────────────────────────────────────────
-- Вычисляемые поля (view для стриков)
-- Стрики считаются на уровне приложения или через функцию
-- ──────────────────────────────────────────

-- Вспомогательная функция: текущий стрик привычки
CREATE OR REPLACE FUNCTION current_streak(p_habit_id UUID, p_today DATE)
RETURNS INTEGER AS $$
DECLARE
    streak INTEGER := 0;
    check_date DATE := p_today;
BEGIN
    LOOP
        IF EXISTS (
            SELECT 1 FROM habit_entries
            WHERE habit_id = p_habit_id
              AND date = check_date
              AND completed = TRUE
        ) THEN
            streak := streak + 1;
            check_date := check_date - 1;
        ELSE
            EXIT;
        END IF;
    END LOOP;
    RETURN streak;
END;
$$ LANGUAGE plpgsql STABLE;

-- ──────────────────────────────────────────
-- Аудит (опционально, Phase 2)
-- ──────────────────────────────────────────
CREATE TABLE audit_log (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     UUID         REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(100) NOT NULL,
    table_name  VARCHAR(100),
    record_id   UUID,
    old_data    JSONB,
    new_data    JSONB,
    ip_address  INET,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user_id   ON audit_log(user_id);
CREATE INDEX idx_audit_created   ON audit_log(created_at DESC);
```

### 6.4 Миграции

```
migrations/
  001_init_extensions.up.sql
  001_init_extensions.down.sql
  002_create_users.up.sql
  002_create_users.down.sql
  003_create_sessions.up.sql
  ...
  010_create_audit_log.up.sql
```

Автоматический запуск при старте backend:
```go
// cmd/server/main.go
m, _ := migrate.New("embed://migrations", dsn)
m.Up() // idempotent
```

---

## 7. REST API

### 7.1 Общие принципы

- Base URL: `/api/v1/`
- Content-Type: `application/json`
- Аутентификация: `Authorization: Bearer <access_token>`
- Пагинация: `?page=1&limit=20` (cursor-based для entries)
- Ошибки:
```json
{
  "error": {
    "code": "HABIT_NOT_FOUND",
    "message": "Привычка не найдена",
    "details": {}
  }
}
```

### 7.2 Эндпоинты

#### Auth

```
POST   /api/v1/auth/register          Регистрация
POST   /api/v1/auth/login             Вход → access + refresh tokens
POST   /api/v1/auth/refresh           Обновление access token
POST   /api/v1/auth/logout            Инвалидация refresh token
POST   /api/v1/auth/logout-all        Инвалидация всех сессий пользователя
POST   /api/v1/auth/recover           Вход по recovery code → смена пароля
GET    /api/v1/auth/sessions          Список активных сессий
DELETE /api/v1/auth/sessions/:id      Отзыв конкретной сессии
```

#### Users / Profile

```
GET    /api/v1/me                     Профиль текущего пользователя
PATCH  /api/v1/me                     Обновление профиля (display_name, timezone, etc.)
PATCH  /api/v1/me/password            Смена пароля
DELETE /api/v1/me                     Удаление аккаунта (с паролем)
GET    /api/v1/me/recovery-codes      Показать кол-во оставшихся кодов (не сами коды)
POST   /api/v1/me/recovery-codes      Сгенерировать новые коды (требует текущий пароль)
```

#### Categories

```
GET    /api/v1/categories             Список категорий пользователя
POST   /api/v1/categories             Создать категорию
GET    /api/v1/categories/:id         Получить категорию
PUT    /api/v1/categories/:id         Обновить категорию
DELETE /api/v1/categories/:id         Удалить категорию
PATCH  /api/v1/categories/reorder     Изменить порядок (массив ID)
```

#### Habits

```
GET    /api/v1/habits                 Список привычек (?category=&archived=false)
POST   /api/v1/habits                 Создать привычку
GET    /api/v1/habits/:id             Получить привычку
PUT    /api/v1/habits/:id             Обновить привычку
DELETE /api/v1/habits/:id             Удалить привычку (каскадно)
PATCH  /api/v1/habits/:id/archive     Архивировать / разархивировать
PATCH  /api/v1/habits/reorder         Изменить порядок (массив ID)
GET    /api/v1/habits/:id/stats       Статистика привычки (?from=&to=)
GET    /api/v1/habits/:id/streak      Текущий + максимальный стрик
```

#### Entries

```
GET    /api/v1/entries                Записи за период (?date=2025-06-21 или ?from=&to=)
POST   /api/v1/entries                Создать / обновить запись (upsert по habit_id+date)
PUT    /api/v1/entries/:id            Обновить запись
DELETE /api/v1/entries/:id            Удалить запись (обнуление)
GET    /api/v1/board/:date            Доска: все привычки + их статус на конкретную дату
```

#### Dashboard / Stats

```
GET    /api/v1/dashboard              Сводка: сегодня, стрики, completion rate
GET    /api/v1/stats/overview         Общая статистика (?period=7d|30d|90d|custom)
GET    /api/v1/stats/heatmap          Тепловая карта (?year=2025)
```

#### System

```
GET    /healthz                       Liveness probe
GET    /readyz                        Readiness probe (DB check)
GET    /metrics                       Prometheus метрики
GET    /api/v1/version                Версия приложения
```

### 7.3 Модели запросов/ответов (примеры)

```typescript
// POST /api/v1/habits
{
  "name": "Медитация",
  "type": "duration",
  "category_id": "uuid",
  "target_value": 20,
  "unit": "мин",
  "color": "#8B5CF6",
  "icon": "brain",
  "frequency": "daily"
}

// GET /api/v1/board/2025-06-21
{
  "date": "2025-06-21",
  "is_editable": true,
  "progress": { "done": 3, "total": 7 },
  "habits": [
    {
      "id": "uuid",
      "name": "Медитация",
      "type": "duration",
      "target_value": 20,
      "unit": "мин",
      "color": "#8B5CF6",
      "icon": "brain",
      "streak": 5,
      "entry": {
        "id": "uuid",
        "completed": true,
        "value": 22,
        "note": null
      }
    }
  ]
}
```

---

## 8. Frontend — UI/UX Спецификация

### 8.1 Дизайн-система

**Палитра** (тёмная тема — основная, светлая — опциональная):

```
Background:  #0F0F12  (почти чёрный, не чисто чёрный)
Surface:     #18181C  (карточки, панели)
Surface+1:   #222228  (hover, активные состояния)
Border:      #2E2E38  (разделители)
Text-primary:  #F2F2F4
Text-secondary: #9292A0
Accent:      #6366F1  (индиго — основной акцент, настраиваемый)
Accent-light:#818CF8
Success:     #22C55E
Warning:     #F59E0B
Error:       #EF4444
```

**Типографика:**

- Display / заголовки: **Inter** (variable) — 600–700 weight
- Body: **Inter** — 400–500 weight
- Mono (значения, даты): **JetBrains Mono** variable

**Радиусы и тени:**
```
--radius-sm:  4px
--radius-md:  8px
--radius-lg:  12px
--radius-xl:  16px
--shadow-sm:  0 1px 3px rgba(0,0,0,0.4)
--shadow-md:  0 4px 16px rgba(0,0,0,0.5)
```

**Уникальный элемент:** "Пульс стрика" — при текущем стрике ≥ 7 дней иконка привычки получает мягкое свечение в цвет привычки (box-shadow + keyframe animation). Это единственная активная анимация в интерфейсе.

### 8.2 Навигация

**Мобиль (< 768px):** Нижний tab bar (Bottom Navigation)

```
[◫ Сегодня]  [📊 Статистика]  [⊞ Привычки]  [⚙ Настройки]
```

**Десктоп (≥ 768px):** Левый сайдбар, коллапсируемый

```
┌──────────┐  ┌────────────────────────────┐
│ HabitFlow│  │  Основной контент           │
│          │  │                             │
│ ◫ Сегодня│  │                             │
│ 📊 Стат  │  │                             │
│ ⊞ Привы  │  │                             │
│          │  │                             │
│ ⚙ Настр  │  │                             │
└──────────┘  └────────────────────────────┘
```

### 8.3 Экраны

#### Экран 1: Доска (главный)

```
┌────────────────────────────────────┐
│  ◁  Вс 21 июня  ▷  [Сегодня]      │
│  ████████░░ 5 из 7                 │
├────────────────────────────────────┤
│  🧠 Медитация          22 мин ✓   │
│  ──────────────────────────────── │
│  💧 Вода               6/8 ст     │
│      [–]  [6]  [+]                 │
│  ──────────────────────────────── │
│  🏃 Пробежка                   ✓  │
│  ──────────────────────────────── │
│  📖 Чтение             45 мин ✓   │
│  ──────────────────────────────── │
│  🔒 Сон (вчера)   8ч 20мин  🔒   │  ← только если дата = вчера
│  ──────────────────────────────── │
│  [+ Добавить привычку]            │
└────────────────────────────────────┘
```

- Навигационная стрелка влево: активна в пределах `edit_window_days`
- За пределами окна — стрелка влево есть, но запись read-only с иконкой 🔒
- Стрелка вправо: только если дата < today
- Кнопка «Сегодня» появляется при навигации в прошлое

#### Экран 2: Список привычек (управление)

```
┌────────────────────────────────────┐
│  Привычки                [+ Новая] │
│  ──────────────────────────────── │
│  [Все] [Здоровье] [Продуктивность] │
│  ──────────────────────────────── │
│  ≡ 🧠 Медитация          5🔥 ···  │
│  ≡ 💧 Вода               12🔥 ··· │
│  ≡ 🏃 Пробежка           0   ···  │
│  ──────────────────────────────── │
│  Архив (2)          [раскрыть ▼]  │
└────────────────────────────────────┘
```

#### Экран 3: Детали привычки / Статистика

```
┌────────────────────────────────────┐
│  ← 🧠 Медитация              [✎]  │
│  ──────────────────────────────── │
│  Текущий стрик  5 дней  🔥         │
│  Максимум      23 дня              │
│  За 30 дней    73% (22/30)         │
│  ──────────────────────────────── │
│  Июнь 2025                        │
│  Пн Вт Ср Чт Пт Сб Вс            │
│  ·  ·  ■  ■  ■  ■  ■              │  ← GitHub heatmap
│  ■  ■  ■  ■  ■  □  ■              │
│  ■  ■  ■  ·  ·  ·  ·              │
│  ──────────────────────────────── │
│  [График за 90 дней ▼]            │
└────────────────────────────────────┘
```

#### Экран 4: Статистика (общая)

- Completion rate сегодня / неделя / месяц (3 карточки)
- Top-5 привычек по стрику
- Тепловая карта года (52 недели × 7 дней)
- Line chart — % выполнения по дням за последние 30 дней

### 8.4 Мобильные особенности (iPhone)

- Вся интерактивная зона кнопок ≥ 44pt
- Bottom Navigation на fixed позиции с учётом `safe-area-inset-bottom`
- Swipe-to-navigate (влево/вправо по датам на экране доски) через touch events
- Числовой ввод для numeric привычек открывает числовую клавиатуру (`inputmode="numeric"`)
- PWA manifest: добавить в Home Screen → запускается без адресной строки

### 8.5 Анимации и переходы

- Отметка boolean: brief "bounce" + цветовой flash (50ms)
- Переход между датами: slide (100ms ease-out)
- Загрузка: skeleton screens (не спиннеры)
- Новая привычка появляется с fade-in
- Всё остальное: без анимаций

---

## 9. Аутентификация и безопасность

### 9.1 Flow аутентификации

```
Клиент                          Сервер
   │                               │
   │  POST /auth/login             │
   │  { username, password }       │
   │ ─────────────────────────►   │
   │                               │  verify argon2id
   │                               │  generate access JWT (15m, RS256)
   │                               │  generate refresh token (UUID)
   │                               │  store refresh hash in sessions
   │  { access_token, refresh_token } │
   │ ◄─────────────────────────── │
   │                               │
   │  GET /api/v1/board/today      │
   │  Authorization: Bearer {at}   │
   │ ─────────────────────────►   │
   │                               │  verify JWT signature + exp
   │  200 { board data }           │
   │ ◄─────────────────────────── │
   │                               │
   │  POST /auth/refresh           │
   │  { refresh_token }            │
   │ ─────────────────────────►   │
   │                               │  verify refresh hash in DB
   │                               │  check not revoked, not expired
   │                               │  issue new access_token
   │                               │  rotate refresh_token (old → revoked)
   │  { access_token, refresh_token } │
   │ ◄─────────────────────────── │
```

### 9.2 Хранение токенов на клиенте

- `access_token`: только в памяти (JavaScript variable, не localStorage)
- `refresh_token`: `HttpOnly; Secure; SameSite=Strict` cookie

### 9.3 Защита от атак

| Угроза | Контрмера |
|---|---|
| Brute-force на login | Rate limit: 5 попыток / 15 мин / IP |
| XSS | CSP headers; access token не в storage |
| CSRF | SameSite=Strict cookie; CORS whitelist |
| SQL injection | Параметризованные запросы (sqlc) |
| Timing attacks | Постоянное время argon2id verify |
| Token theft | Refresh rotation (использованный токен → немедленный revoke всех сессий) |

### 9.4 Kubernetes Secrets

```yaml
# Не в репозитории — создаётся при деплойменте
apiVersion: v1
kind: Secret
metadata:
  name: habitflow-secrets
  namespace: habitflow
stringData:
  DB_PASSWORD: "..."
  JWT_PRIVATE_KEY: |
    -----BEGIN EC PRIVATE KEY-----
    ...
  JWT_PUBLIC_KEY: |
    -----BEGIN PUBLIC KEY-----
    ...
```

---

## 10. Мониторинг и логирование

### 10.1 Метрики (Prometheus)

Backend экспортирует на `:9090/metrics`:

```
# HTTP метрики
habitflow_http_requests_total{method, path, status}      counter
habitflow_http_request_duration_seconds{method, path}    histogram (buckets: 10ms,50ms,100ms,200ms,500ms,1s,5s)
habitflow_http_requests_in_flight                        gauge

# Бизнес-метрики
habitflow_habit_entries_created_total{type}              counter
habitflow_active_users_total                             gauge
habitflow_habits_total{archived}                         gauge
habitflow_streak_current_max                             gauge

# База данных (pgx pool)
habitflow_db_connections_total                           gauge
habitflow_db_query_duration_seconds{query}               histogram

# Go runtime
go_goroutines, go_memstats_* (стандартные)
```

### 10.2 Grafana Dashboards

**Dashboard 1: Application Overview**
- RPS по эндпоинтам (line chart)
- Latency p50/p95/p99 (line chart)
- Error rate (% 5xx) (stat + time series)
- Active users (gauge)
- DB connection pool utilization

**Dashboard 2: Business Metrics**
- Новые записи в день
- Топ привычек по активности
- Completion rate общий
- Распределение типов привычек

**Dashboard 3: Infrastructure**
- CPU / Memory по подам
- PVC utilization (PostgreSQL)
- Pod restarts

Dashboards хранятся как JSON в `helm/charts/habitflow/dashboards/` и монтируются через ConfigMap.

### 10.3 Логирование (Loki)

Все компоненты пишут структурированный JSON в stdout:

```json
{
  "timestamp": "2025-06-21T10:00:00.000Z",
  "level": "info",
  "service": "habitflow-backend",
  "version": "1.2.3",
  "trace_id": "abc123",
  "user_id": "uuid",
  "method": "POST",
  "path": "/api/v1/entries",
  "status": 201,
  "duration_ms": 12,
  "message": "entry created"
}
```

Grafana Alloy собирает логи с подов по label `app=habitflow-backend` и отправляет в Loki.

**Loki запросы (в Grafana):**
```
{app="habitflow-backend"} | json | level="error"
{app="habitflow-backend"} | json | duration_ms > 500
{app="habitflow-backend"} | json | path=~"/auth/login" | status >= 400
```

### 10.4 Алерты (Alertmanager)

```yaml
groups:
- name: habitflow
  rules:
  - alert: HighErrorRate
    expr: rate(habitflow_http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    labels:
      severity: warning

  - alert: HighLatency
    expr: histogram_quantile(0.95, habitflow_http_request_duration_seconds_bucket) > 0.5
    for: 5m

  - alert: DBConnectionsExhausted
    expr: habitflow_db_connections_total > 45  # limit=50
    for: 2m

  - alert: PodNotReady
    expr: kube_pod_status_ready{namespace="habitflow", condition="true"} == 0
    for: 2m
    labels:
      severity: critical

  - alert: DiskAlmostFull
    expr: kubelet_volume_stats_available_bytes{namespace="habitflow"} / kubelet_volume_stats_capacity_bytes < 0.15
    for: 10m
```

---

## 11. Helm Chart и Kubernetes манифесты

### 11.1 Структура Helm Chart

```
helm/
└── habitflow/
    ├── Chart.yaml
    ├── values.yaml
    ├── values.production.yaml         ← переопределения для home lab
    ├── charts/                        ← зависимости
    │   └── postgresql-15.x.x.tgz    ← bitnami/postgresql
    ├── templates/
    │   ├── _helpers.tpl
    │   ├── NOTES.txt
    │   ├── namespace.yaml
    │   ├── backend/
    │   │   ├── deployment.yaml
    │   │   ├── service.yaml
    │   │   ├── hpa.yaml
    │   │   ├── pdb.yaml
    │   │   └── servicemonitor.yaml
    │   ├── frontend/
    │   │   ├── deployment.yaml
    │   │   ├── service.yaml
    │   │   └── configmap-nginx.yaml
    │   ├── ingress.yaml
    │   ├── secrets.yaml               ← ExternalSecret или direct
    │   ├── configmap-app.yaml
    │   ├── cronjob-backup.yaml
    │   └── grafana-dashboard-cm.yaml
    └── dashboards/
        ├── overview.json
        └── business.json
```

### 11.2 values.yaml (выдержка)

```yaml
global:
  domain: habitflow.local
  tls:
    enabled: true
    clusterIssuer: selfsigned-cluster-issuer

backend:
  image:
    repository: ghcr.io/smirnofflab/habitflow-backend
    tag: "1.0.0"
    pullPolicy: IfNotPresent
  replicas: 1
  resources:
    requests:
      cpu: "50m"
      memory: "64Mi"
    limits:
      cpu: "500m"
      memory: "256Mi"
  config:
    logLevel: info
    jwtAccessExpiry: "15m"
    jwtRefreshExpiry: "720h"   # 30 дней
    editWindowDaysDefault: 1
    dbPoolSize: 10
  hpa:
    enabled: true
    minReplicas: 1
    maxReplicas: 3
    targetCPUUtilizationPercentage: 70

frontend:
  image:
    repository: ghcr.io/smirnofflab/habitflow-frontend
    tag: "1.0.0"
  replicas: 1
  resources:
    requests:
      cpu: "10m"
      memory: "32Mi"
    limits:
      cpu: "100m"
      memory: "64Mi"

postgresql:
  enabled: true
  auth:
    database: habitflow
    username: habitflow
    # password из Secret
  primary:
    persistence:
      enabled: true
      size: 5Gi
      storageClass: "local-path"

backup:
  enabled: true
  schedule: "0 3 * * *"     # 03:00 каждую ночь
  retention: 7               # хранить 7 дампов
  pvc:
    size: 2Gi

monitoring:
  serviceMonitor:
    enabled: true
    namespace: monitoring
  grafanaDashboard:
    enabled: true
    namespace: monitoring
    label:
      grafana_dashboard: "1"
```

### 11.3 Backend Deployment (шаблон)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "habitflow.fullname" . }}-backend
  labels: {{ include "habitflow.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.backend.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/component: backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    spec:
      serviceAccountName: {{ include "habitflow.fullname" . }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: backend
        image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: DB_HOST
          value: {{ include "habitflow.postgresql.host" . }}
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: habitflow-secrets
              key: DB_PASSWORD
        - name: JWT_PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: habitflow-secrets
              key: JWT_PRIVATE_KEY
        envFrom:
        - configMapRef:
            name: {{ include "habitflow.fullname" . }}-config
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          failureThreshold: 3
        resources: {{ toYaml .Values.backend.resources | nindent 10 }}
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
```

### 11.4 Docker образы

**Backend (multi-stage):**
```dockerfile
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w -X main.Version=${VERSION}" -o server ./cmd/server

FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/server /server
COPY --from=builder /app/migrations /migrations
EXPOSE 8080 9090
USER 1000
ENTRYPOINT ["/server"]
```

**Frontend (multi-stage):**
```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --frozen-lockfile
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
EXPOSE 3000
ENTRYPOINT ["/docker-entrypoint.sh"]
```

---

## 12. Структура репозитория

```
habitflow/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # lint, test, build
│       └── release.yml             # tag → build + push images
│
├── backend/                        # Go
│   ├── cmd/
│   │   └── server/
│   │       └── main.go
│   ├── internal/
│   │   ├── api/
│   │   │   ├── handler/            # HTTP handlers
│   │   │   │   ├── auth.go
│   │   │   │   ├── habits.go
│   │   │   │   ├── entries.go
│   │   │   │   └── stats.go
│   │   │   ├── middleware/
│   │   │   │   ├── auth.go
│   │   │   │   ├── ratelimit.go
│   │   │   │   └── logging.go
│   │   │   └── router.go
│   │   ├── domain/                 # бизнес-сущности (без зависимостей)
│   │   │   ├── habit.go
│   │   │   ├── entry.go
│   │   │   └── user.go
│   │   ├── service/                # бизнес-логика
│   │   │   ├── auth.go
│   │   │   ├── habits.go
│   │   │   └── stats.go
│   │   ├── repository/             # слой данных
│   │   │   ├── postgres/
│   │   │   │   ├── queries/        # .sql файлы для sqlc
│   │   │   │   │   ├── habits.sql
│   │   │   │   │   ├── entries.sql
│   │   │   │   │   └── auth.sql
│   │   │   │   ├── db.go           # sqlc-generated
│   │   │   │   └── models.go       # sqlc-generated
│   │   │   └── interfaces.go
│   │   ├── config/
│   │   │   └── config.go
│   │   └── metrics/
│   │       └── metrics.go
│   ├── migrations/                 # SQL файлы (embed)
│   ├── sqlc.yaml
│   ├── go.mod
│   ├── go.sum
│   └── Dockerfile
│
├── frontend/                       # React / TypeScript
│   ├── src/
│   │   ├── app/                    # роутинг, провайдеры
│   │   ├── pages/
│   │   │   ├── Board/
│   │   │   ├── Habits/
│   │   │   ├── Stats/
│   │   │   └── Settings/
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui base
│   │   │   ├── HabitCard/
│   │   │   ├── Board/
│   │   │   ├── HeatMap/
│   │   │   └── ...
│   │   ├── api/                    # typed API client
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── habits.ts
│   │   │   └── types.ts            # из OpenAPI spec
│   │   ├── store/                  # Zustand stores
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── i18n/
│   │   │   ├── ru.json
│   │   │   └── en.json
│   │   └── styles/
│   ├── public/
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── package.json
│   └── Dockerfile
│
├── helm/
│   └── habitflow/
│       └── (см. раздел 11.1)
│
├── docs/
│   ├── ТЗ.md                       # этот документ
│   ├── api.yaml                    # OpenAPI 3.1
│   ├── architecture.md
│   └── runbook.md                  # операционные процедуры
│
├── scripts/
│   ├── setup-dev.sh                # локальное окружение
│   ├── generate-keys.sh            # генерация JWT ключей
│   └── seed-db.sh                  # тестовые данные
│
├── docker-compose.yml              # локальная разработка
├── docker-compose.override.yml     # опциональные сервисы (Grafana, Prometheus)
├── Makefile
└── README.md
```

### 12.1 Makefile (основные цели)

```makefile
dev:          # запустить всё через docker-compose
test:         # backend unit + integration тесты
test-e2e:     # Playwright e2e тесты
lint:         # golangci-lint + eslint
generate:     # sqlc generate + openapi generate + i18n extract
build:        # docker build backend + frontend
push:         # push в registry
helm-lint:    # helm lint + kubeval
helm-diff:    # helm diff перед деплоем
deploy:       # helm upgrade --install
port-forward: # kubectl port-forward для локального доступа к БД
backup-now:   # ручной запуск job резервного копирования
logs:         # kubectl logs -f всех подов
```

---

## 13. Стратегия тестирования

### 13.1 Уровни тестирования

```
        ▲ Меньше, медленнее, дороже
        │
        │  ┌─────────────────────┐
        │  │    E2E тесты         │  Playwright
        │  │  (критичные сценарии)│
        │  └─────────────────────┘
        │  ┌─────────────────────────────┐
        │  │  Integration / API тесты    │  httptest + testcontainers-go
        │  │  (handlers + DB)            │
        │  └─────────────────────────────┘
        │  ┌────────────────────────────────────────┐
        │  │       Unit тесты                        │  Go test + Vitest
        │  │  (service layer, utils, components)     │
        │  └────────────────────────────────────────┘
        ▼ Больше, быстрее, дешевле
```

### 13.2 Backend тесты (Go)

**Unit тесты — service layer:**
```
backend/internal/service/
  auth_test.go          -- регистрация, логин, refresh, logout
  habits_test.go        -- CRUD, архивирование, сортировка
  stats_test.go         -- расчёт стрика, completion rate
  entries_test.go       -- upsert, window validation
```

**Integration тесты — API handlers:**
```
backend/internal/api/handler/
  auth_test.go          -- полный flow с реальной БД (testcontainers)
  habits_test.go
  entries_test.go
  -- проверка rate limiting
  -- проверка авторизации (401/403)
```

**Coverage цель:** ≥ 80% для service layer, ≥ 60% для handlers

**Конкретные тест-кейсы (примеры):**

```
TestAuth:
  - регистрация с корректными данными → 201
  - регистрация с дубль-username → 409
  - логин с неверным паролем → 401
  - логин 6 раз подряд → 429 (rate limit)
  - refresh с истёкшим токеном → 401
  - использованный refresh token → 401 + инвалидация сессии

TestEditWindow:
  - запись для сегодня → 200
  - запись для вчера (edit_window=1) → 200
  - запись для позавчера (edit_window=1) → 403
  - запись для будущего → 403
  - изменение edit_window на 7 → запись для 6 дней назад → 200

TestStreak:
  - 5 дней подряд → streak=5
  - пропуск 1 дня → streak=0
  - boolean habit: completed=false не считается
  - numeric habit: value >= target → completed
```

### 13.3 Frontend тесты (Vitest + Testing Library)

```
src/
  components/
    HabitCard/
      HabitCard.test.tsx     -- рендер, toggle, значение
    Board/
      Board.test.tsx         -- навигация по датам, блокировка
    HeatMap/
      HeatMap.test.tsx       -- корректная разметка дней

  utils/
    streak.test.ts           -- расчёт стрика
    dateWindow.test.ts       -- isEditable(date, windowDays)
    formatters.test.ts       -- форматирование значений

  store/
    boardStore.test.ts       -- навигация, оптимистичные обновления
```

**Coverage цель:** ≥ 70% для utilities, ≥ 50% для components

### 13.4 E2E тесты (Playwright)

```
e2e/
  auth.spec.ts
    - регистрация → вход → выход
    - восстановление по recovery code
    - защищённые маршруты без токена

  board.spec.ts
    - отметить boolean привычку
    - ввести значение для numeric привычки
    - навигация к предыдущему дню
    - попытка редактировать заблокированный день

  habits.spec.ts
    - создание привычки всех трёх типов
    - архивирование → исчезновение из доски
    - drag & drop сортировка

  mobile.spec.ts
    - запустить в viewport 390×844 (iPhone 14)
    - bottom navigation
    - swipe навигация по датам
    - touch-friendly ввод значений
```

### 13.5 CI Pipeline

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]

jobs:
  backend-test:
    - golangci-lint
    - go test ./... -race -coverprofile=coverage.out
    - Если coverage < 80% → fail
    - go build (проверить компиляцию)

  frontend-test:
    - eslint + tsc --noEmit
    - vitest run --coverage
    - Если coverage < 70% → warning

  e2e:
    needs: [backend-test, frontend-test]
    - docker-compose up -d
    - ждать healthcheck
    - playwright test
    - Сохранить скриншоты как artifacts

  helm-validate:
    - helm lint
    - helm template | kubeval
    - helm template | kube-score

  security-scan:
    - gosec ./...                     # Go SAST
    - trivy image --severity HIGH,CRITICAL (образы)
    - grype sbom (SBOM сканирование)
```

---

## 14. Фазы разработки и MVP

### Phase 0: Основы (неделя 1)
- [ ] Репозиторий, Makefile, docker-compose.yml
- [ ] PostgreSQL + миграции 001-005 (users, habits, entries)
- [ ] Backend: конфигурация, логгер, роутер, healthz/readyz
- [ ] `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- [ ] Frontend: Vite + React + Tailwind + shadcn setup
- [ ] Страница логина / регистрации

### Phase 1: MVP — Доска (недели 2-3)
- [ ] CRUD привычек (только boolean на старте)
- [ ] `GET /api/v1/board/:date`
- [ ] Отметка привычки (toggle)
- [ ] Навигация по датам (стрелки)
- [ ] Edit window validation
- [ ] Прогресс дня (X из N)
- [ ] Базовые стрики

**← Первый рабочий продукт**

### Phase 2: Полноценные привычки (неделя 4)
- [ ] Numeric и Duration типы привычек
- [ ] Категории
- [ ] Drag & drop сортировка
- [ ] Архивирование
- [ ] Recovery codes

### Phase 3: Статистика (неделя 5)
- [ ] Completion rate
- [ ] Страница статистики
- [ ] Heatmap (calendar view)
- [ ] Line chart за 30 дней

### Phase 4: Мониторинг + Helm (неделя 6)
- [ ] Prometheus метрики на backend
- [ ] Helm chart (полный)
- [ ] Grafana dashboards (JSON)
- [ ] Grafana Alloy + Loki
- [ ] Alertmanager rules
- [ ] CronJob backup
- [ ] Деплой в K3s

### Phase 5: Полировка (неделя 7)
- [ ] PWA manifest + service worker
- [ ] Тёмная / светлая тема
- [ ] i18n (ru/en)
- [ ] E2E тесты (Playwright)
- [ ] Мобильная оптимизация (real device testing iPhone)
- [ ] Accessibility audit
- [ ] Документация (README, runbook)

### Phase 6: Nice-to-have (по желанию)
- [ ] Import/Export JSON
- [ ] Weekly/custom frequency
- [ ] Заметки к записям
- [ ] Audit log UI
- [ ] Второй пользователь (multi-user тест)

---

## 15. Открытые вопросы и решения

| Вопрос | Решение |
|---|---|
| Один пользователь или мультиюзер? | Мультиюзер, но без публичной регистрации. Первый зарегистрированный — администратор. Есть CLI-флаг `--disable-registration` для блокировки новых регистраций |
| Как email recovery без SMTP? | 8 одноразовых recovery codes при регистрации. Пользователь сохраняет их локально |
| TLS в домашней сети? | cert-manager с self-signed ClusterIssuer. Браузер потребует однократно принять сертификат |
| Hostname для Ingress? | `habitflow.local` — добавить в `/etc/hosts` или настроить локальный DNS (Pi-hole/AdGuard Home) |
| Timezone сервера vs пользователя? | Сервер хранит всё в UTC. День определяется по timezone пользователя при запросе |
| Offline-режим? | PWA кэширует статику. API-запросы — только онлайн |
| Масштабирование PostgreSQL? | Одна реплика достаточна для домашнего использования. PgBouncer — опционально |
| Harbor vs ghcr.io? | ghcr.io проще. Harbor — если нужна полная изоляция от интернета |
| VPN-доступ? | Настройка WireGuard/Tailscale на роутере — вне скоупа этого ТЗ, но Ingress hostname должен резолвиться в VPN-сети |

---

## Appendix A: Локальная разработка

```bash
# Предварительные требования: Docker, Node 22, Go 1.23, kubectl, helm

git clone https://github.com/smirnofflab/habitflow
cd habitflow

# Генерация JWT ключей
./scripts/generate-keys.sh

# Запуск всей инфраструктуры
make dev

# Приложение: http://localhost:3000
# API docs: http://localhost:8080/swagger/
# Grafana: http://localhost:3001 (admin/admin)

# Тесты
make test
make test-e2e
```

## Appendix B: Команды деплоя

```bash
# Первый деплой
kubectl create namespace habitflow
kubectl create secret generic habitflow-secrets \
  --from-literal=DB_PASSWORD="$(openssl rand -base64 32)" \
  --from-file=JWT_PRIVATE_KEY=./secrets/jwt.key \
  --from-file=JWT_PUBLIC_KEY=./secrets/jwt.pub \
  -n habitflow

helm dependency update ./helm/habitflow
helm install habitflow ./helm/habitflow \
  -f ./helm/habitflow/values.production.yaml \
  -n habitflow

# Обновление (rolling update)
helm upgrade habitflow ./helm/habitflow \
  --set backend.image.tag=1.1.0 \
  -n habitflow

# Откат
helm rollback habitflow 1 -n habitflow

# Просмотр статуса
helm status habitflow -n habitflow
kubectl get pods -n habitflow -w
```

## Appendix C: Runbook — основные операции

```bash
# Ручной бэкап
kubectl create job --from=cronjob/habitflow-backup backup-manual-$(date +%Y%m%d) -n habitflow

# Просмотр логов
kubectl logs -l app.kubernetes.io/name=habitflow-backend -n habitflow --tail=100 -f

# Подключение к БД
kubectl exec -it statefulset/habitflow-postgresql -n habitflow -- psql -U habitflow -d habitflow

# Сброс пароля (admin CLI)
kubectl exec deploy/habitflow-backend -n habitflow -- /server reset-password --username=admin

# Проверка метрик
kubectl port-forward svc/habitflow-backend 9090:9090 -n habitflow
# curl http://localhost:9090/metrics
```

---

*HabitFlow ТЗ v1.0 — Smirnoff Lab — 2026*
