from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import Any, Dict, Optional, cast

import httpx

from .exceptions import TaskForceAIError

DEFAULT_BASE_URL = "https://taskforceai.chat/api/developer"
JsonDict = Dict[str, Any]


def _extract_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            error_payload = cast(Dict[str, Any], data)
            error_value = error_payload.get("error")
            if isinstance(error_value, str):
                return error_value
            if error_value is not None:
                return str(error_value)
    except ValueError:
        pass

    text = response.text
    return text or f"HTTP {response.status_code}"


class TaskForceAIClient:
    """Synchronous TaskForceAI client."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        if not api_key.strip():
            raise TaskForceAIError("API key must be a non-empty string")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def __enter__(self) -> "TaskForceAIClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[JsonDict] = None,
    ) -> JsonDict:
        url = f"{self._base_url}{endpoint}"
        try:
            response = self._client.request(
                method=method,
                url=url,
                json=json,
                headers=self._headers(),
                timeout=self._timeout,
            )
            response.raise_for_status()
            return cast(JsonDict, response.json())
        except httpx.TimeoutException as exc:
            raise TaskForceAIError("Request timeout") from exc
        except httpx.HTTPStatusError as exc:
            message = _extract_error_message(exc.response)
            raise TaskForceAIError(message, status_code=exc.response.status_code) from exc
        except httpx.HTTPError as exc:
            raise TaskForceAIError(f"Network error: {exc}") from exc

    def submit_task(
        self,
        prompt: str,
        *,
        silent: bool = False,
        mock: bool = False,
        open_router_key: Optional[str] = None,
    ) -> str:
        if not prompt.strip():
            raise TaskForceAIError("Prompt must be a non-empty string")

        payload: JsonDict = {"prompt": prompt, "options": {"silent": silent, "mock": mock}}
        if open_router_key:
            payload["openRouterKey"] = open_router_key

        data = self._request("POST", "/run", json=payload)
        task_id = data.get("taskId")
        if not isinstance(task_id, str):
            raise TaskForceAIError("API did not return a taskId")
        return task_id

    def get_task_status(self, task_id: str) -> JsonDict:
        if not task_id.strip():
            raise TaskForceAIError("Task ID must be a non-empty string")
        return self._request("GET", f"/status/{task_id}")

    def get_task_result(self, task_id: str) -> JsonDict:
        if not task_id.strip():
            raise TaskForceAIError("Task ID must be a non-empty string")
        return self._request("GET", f"/results/{task_id}")

    def wait_for_completion(
        self,
        task_id: str,
        *,
        poll_interval: float = 2.0,
        max_attempts: int = 150,
    ) -> JsonDict:
        for _ in range(max_attempts):
            status = self.get_task_status(task_id)
            state = status.get("status")

            if state == "completed" and "result" in status:
                return {"taskId": task_id, "result": status["result"]}

            if state == "failed":
                detail = status.get("error") or "Task failed"
                raise TaskForceAIError(detail)

            time.sleep(poll_interval)

        raise TaskForceAIError("Task did not complete within the expected time")

    def run_task(
        self,
        prompt: str,
        *,
        silent: bool = False,
        mock: bool = False,
        open_router_key: Optional[str] = None,
        poll_interval: float = 2.0,
        max_attempts: int = 150,
    ) -> JsonDict:
        task_id = self.submit_task(
            prompt,
            silent=silent,
            mock=mock,
            open_router_key=open_router_key,
        )
        return self.wait_for_completion(
            task_id,
            poll_interval=poll_interval,
            max_attempts=max_attempts,
        )


class AsyncTaskForceAIClient:
    """Asynchronous TaskForceAI client."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        if not api_key.strip():
            raise TaskForceAIError("API key must be a non-empty string")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout, transport=transport)

    async def __aenter__(self) -> "AsyncTaskForceAIClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[JsonDict] = None,
    ) -> JsonDict:
        url = f"{self._base_url}{endpoint}"
        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=json,
                headers=self._headers(),
                timeout=self._timeout,
            )
            response.raise_for_status()
            return cast(JsonDict, response.json())
        except httpx.TimeoutException as exc:
            raise TaskForceAIError("Request timeout") from exc
        except httpx.HTTPStatusError as exc:
            message = _extract_error_message(exc.response)
            raise TaskForceAIError(message, status_code=exc.response.status_code) from exc
        except httpx.HTTPError as exc:
            raise TaskForceAIError(f"Network error: {exc}") from exc

    async def submit_task(
        self,
        prompt: str,
        *,
        silent: bool = False,
        mock: bool = False,
        open_router_key: Optional[str] = None,
    ) -> str:
        if not prompt.strip():
            raise TaskForceAIError("Prompt must be a non-empty string")

        payload: JsonDict = {"prompt": prompt, "options": {"silent": silent, "mock": mock}}
        if open_router_key:
            payload["openRouterKey"] = open_router_key

        data = await self._request("POST", "/run", json=payload)
        task_id = data.get("taskId")
        if not isinstance(task_id, str):
            raise TaskForceAIError("API did not return a taskId")
        return task_id

    async def get_task_status(self, task_id: str) -> JsonDict:
        if not task_id.strip():
            raise TaskForceAIError("Task ID must be a non-empty string")
        return await self._request("GET", f"/status/{task_id}")

    async def get_task_result(self, task_id: str) -> JsonDict:
        if not task_id.strip():
            raise TaskForceAIError("Task ID must be a non-empty string")
        return await self._request("GET", f"/results/{task_id}")

    async def wait_for_completion(
        self,
        task_id: str,
        *,
        poll_interval: float = 2.0,
        max_attempts: int = 150,
    ) -> JsonDict:
        for _ in range(max_attempts):
            status = await self.get_task_status(task_id)
            state = status.get("status")

            if state == "completed" and "result" in status:
                return {"taskId": task_id, "result": status["result"]}

            if state == "failed":
                detail = status.get("error") or "Task failed"
                raise TaskForceAIError(detail)

            await asyncio.sleep(poll_interval)

        raise TaskForceAIError("Task did not complete within the expected time")

    async def run_task(
        self,
        prompt: str,
        *,
        silent: bool = False,
        mock: bool = False,
        open_router_key: Optional[str] = None,
        poll_interval: float = 2.0,
        max_attempts: int = 150,
    ) -> JsonDict:
        task_id = await self.submit_task(
            prompt,
            silent=silent,
            mock=mock,
            open_router_key=open_router_key,
        )
        return await self.wait_for_completion(
            task_id,
            poll_interval=poll_interval,
            max_attempts=max_attempts,
        )
