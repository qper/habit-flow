python3 - << 'PYEOF'
with open('/Users/qper/git/github/qper/habit-flow/HabitFlow.py', 'r') as f:
    content = f.read()

# ──────────────────────────────────────────────────────────────
# Replace _post with smart version + add _post_issue_with_retry
# ──────────────────────────────────────────────────────────────
old_post = '''    def _post(self, path: str, data: dict) -> dict:
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
                return json.loads(r.read().decode()) if r.length else {}'''

new_post = '''    def _post(self, path: str, data: dict) -> dict:
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

    def _post_issue(self, fields: dict) -> dict:
        """Создать issue с автоматическим retry при неизвестных customfield_*.

        Jira возвращает 400 с errors={customfield_NNNNN: "not on screen"} —
        в этом случае убираем проблемные поля и повторяем запрос.
        """
        import copy
        payload = {"fields": copy.deepcopy(fields)}
        for attempt in range(4):  # максимум 4 попытки (каждый раз убираем 1+ поле)
            try:
                if HAS_REQUESTS:
                    resp = self.session.post(
                        f"{self.base_url}/rest/api/3/issue", json=payload, timeout=30
                    )
                    if resp.status_code == 400:
                        body = resp.json()
                        errors: dict = body.get("errors", {})
                        bad_fields = [k for k in errors if k.startswith("customfield_")]
                        if bad_fields:
                            for bf in bad_fields:
                                log.warning(
                                    "    Поле %s недоступно на экране создания — пропускаю.", bf
                                )
                                payload["fields"].pop(bf, None)
                            continue  # повторить без этих полей
                    resp.raise_for_status()
                    return resp.json() if resp.content else {}
                else:
                    # urllib fallback — без детального retry
                    body_bytes = json.dumps(payload).encode()
                    req = urllib.request.Request(
                        f"{self.base_url}/rest/api/3/issue",
                        data=body_bytes, method="POST",
                        headers={
                            "Authorization": self._auth_header,
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        }
                    )
                    with urllib.request.urlopen(req, timeout=30) as r:
                        return json.loads(r.read().decode()) if r.length else {}
            except Exception as exc:
                if attempt == 3:
                    raise
                log.debug("    Retry %d: %s", attempt + 1, exc)
        raise RuntimeError("Не удалось создать тикет после нескольких попыток")

    def discover_sprint_field(self, project_key: str) -> str:
        """Найти ID кастомного поля Sprint через create-meta.

        Возвращает имя поля вида 'customfield_10020' (или другое).
        Кэшируется в self._sprint_field.
        """
        if hasattr(self, "_sprint_field"):
            return self._sprint_field

        self._sprint_field = "customfield_10020"  # default

        try:
            # Современный Jira Cloud API v3 createmeta
            data = self._get(
                f"/rest/api/3/issue/createmeta"
                f"?projectKeys={project_key}&issuetypeNames=Story"
                f"&expand=projects.issuetypes.fields"
            )
            projects = data.get("projects", [])
            for proj in projects:
                for it in proj.get("issuetypes", []):
                    for field_id, field_def in it.get("fields", {}).items():
                        fname = field_def.get("name", "").lower()
                        if "sprint" in fname and field_id.startswith("customfield_"):
                            log.debug("    Обнаружено поле Sprint: %s (%s)", field_id, field_def["name"])
                            self._sprint_field = field_id
                            return self._sprint_field
        except Exception as exc:
            log.debug("    discover_sprint_field: %s", exc)

        log.debug("    Используется Sprint field по умолчанию: %s", self._sprint_field)
        return self._sprint_field'''

if old_post in content:
    content = content.replace(old_post, new_post)
    print("✅ _post и вспомогательные методы обновлены")
else:
    print("❌ Паттерн _post не найден")
    import sys; sys.exit(1)

with open('/Users/qper/git/github/qper/habit-flow/HabitFlow.py', 'w') as f:
    f.write(content)
PYEOF