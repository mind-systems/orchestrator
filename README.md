# Orchestrator

> Автономный оркестратор AI-агентов — планирует, имплементирует и ревьюит задачи из роадмапа.

Orchestrator читает milestone-ы из роадмапа целевого проекта и прогоняет каждый через пятиступенчатый конвейер: Planner составляет план, PlanReviewer проверяет план (с итерациями до принятия), Implementer пишет код, Reviewer проверяет результат (с итерациями до принятия). В конце каждого milestone оркестратор делает git commit и отмечает задачу выполненной.

## Быстрый старт

```bash
cd orchestrator && uv sync
cp orchestrator.json.example orchestrator.json  # затем отредактируйте при необходимости
uv run orchestrator implement /path/to/project
```

Требуется установленный и авторизованный [Claude Code](https://claude.ai/code) CLI.

### Разрешения Claude Code

Агент-планировщик должен иметь право редактировать файлы в `.ai-factory/plans/` — иначе он не сможет исправить план после замечаний ревьюера и цикл зависнет. Добавьте в `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Edit(/Users/<you>/projects/**/.ai-factory/plans/**)",
      "Write(/Users/<you>/projects/**/.ai-factory/plans/**)"
    ]
  }
}
```

Без этого разрешения plan-ревью будет бесконечно возвращать одни и те же замечания — план физически не изменится.

## Режимы работы

| Команда | Что делает |
|---------|-----------|
| `implement` | Планирует и имплементирует все pending-milestone-ы |
| `test` | Пишет тесты по milestone-ам из `ROADMAP_TESTS.md` |


Подробная документация — в [docs/](docs/), индекс страниц — в [CLAUDE.md](CLAUDE.md).

## Лицензия

MIT
