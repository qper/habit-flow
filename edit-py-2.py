python3 - << 'PYEOF'
with open('/Users/qper/git/github/qper/habit-flow/HabitFlow.py', 'r') as f:
    content = f.read()

old_create = '''    def create_issue(
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
        return key'''

new_create = '''    def create_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str,
        parent_key: Optional[str] = None,
        epic_key: Optional[str] = None,     # оставлен для совместимости, не используется
        sprint_id: Optional[int] = None,
        epic_name: Optional[str] = None,    # оставлен для совместимости, не используется
        custom_fields: Optional[dict] = None,
    ) -> str:
        """Создать задачу в Jira. Вернуть ключ созданного тикета (например, HF-42).

        Логика связывания иерархии:
          Epic   — parent не нужен (корневой уровень)
          Story  — parent={"key": epic_key}     (Jira Cloud next-gen / classic)
          Task   — parent={"key": story_key}    (subtask или child issue)

        customfield_10011 (Epic Name) и customfield_10014 (Epic Link) НЕ используются —
        они устарели в современном Jira Cloud и вызывают 400 Bad Request.
        Sprint field обнаруживается автоматически через discover_sprint_field().
        """
        fields: dict = {
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary[:255],
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

        # Иерархия через parent (работает в Jira Cloud classic и next-gen)
        # Epic — корневой, parent не нужен
        # Story → Epic, Task → Story
        if parent_key and issue_type in ("Story", "Task"):
            fields["parent"] = {"key": parent_key}

        # Sprint — используем поле, найденное через create-meta
        if sprint_id is not None:
            sprint_field = self.discover_sprint_field(project_key)
            fields[sprint_field] = sprint_id

        # Дополнительные поля (переданные явно)
        if custom_fields:
            fields.update(custom_fields)

        result = self._post_issue(fields)
        key = result.get("key", "")
        log.info("  ✅ Created %s [%s]: %s", issue_type, key, summary[:60])
        return key'''

if old_create in content:
    content = content.replace(old_create, new_create)
    print("✅ create_issue переписан")
else:
    print("❌ Паттерн create_issue не найден")
    import sys; sys.exit(1)

with open('/Users/qper/git/github/qper/habit-flow/HabitFlow.py', 'w') as f:
    f.write(content)
PYEOF