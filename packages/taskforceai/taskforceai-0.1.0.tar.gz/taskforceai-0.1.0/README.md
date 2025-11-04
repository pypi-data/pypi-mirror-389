# TaskForceAI Python SDK

The official Python client for TaskForceAI's multi-agent orchestration platform.

- ✅ Sync + async clients powered by `httpx`
- ✅ Automatic authentication with your TaskForceAI API key
- ✅ Convenience helpers for polling task completion
- ✅ Rich error handling with status codes and retry-ready exceptions

## Installation

```bash
python -m pip install taskforceai
```

## Quick Start

```python
from taskforceai import TaskForceAIClient

client = TaskForceAIClient(api_key="your-api-key")

task_id = client.submit_task("Analyze the security posture of this repository.")
result = client.wait_for_completion(task_id)

print(result["result"])
```

```python
# Bring your own OpenRouter key (unlocks premium models)
task_id = client.submit_task(
    "Draft a quarterly strategy update.",
    open_router_key="sk-or-your-openrouter-key",
)
```

### Async Variant

```python
import asyncio
from taskforceai import AsyncTaskForceAIClient

async def main() -> None:
    async with AsyncTaskForceAIClient(api_key="your-api-key") as client:
        result = await client.run_task("Summarize the latest launch notes.")
        print(result["result"])

asyncio.run(main())
```

## API Surface

Both clients expose the same methods:

- `submit_task(prompt, *, silent=False, mock=False, open_router_key=None) -> str`
- `get_task_status(task_id) -> dict`
- `get_task_result(task_id) -> dict`
- `wait_for_completion(task_id, poll_interval=2.0, max_attempts=150) -> dict`
- `run_task(prompt, ...) -> dict`

All responses mirror the REST API payloads. Errors raise `TaskForceAIError`, which includes `status_code` for quick branching.

## Development

```bash
python -m pip install -e "packages/python-sdk[dev]"
pytest packages/python-sdk/tests
ruff format packages/python-sdk/src packages/python-sdk/tests -q
ruff check packages/python-sdk/src packages/python-sdk/tests
mypy --config-file packages/python-sdk/pyproject.toml packages/python-sdk/src
```

## License

MIT
