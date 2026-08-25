import asyncio
from datetime import UTC, datetime

from app.core.correlation import get_or_create_correlation_id
from app.integrations.models import IntegrationRequest
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.models import ExecutionStatus, RuntimeExecution, RuntimeRequest
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.runtime.registry import ConnectorRegistry
from app.runtime.store import ExecutionStore


class IntegrationRuntime:
    def __init__(self, *, registry: ConnectorRegistry, store: ExecutionStore,
                 circuit_breaker: CircuitBreaker, rate_limiter: SlidingWindowRateLimiter,
                 backoff_base_seconds: float = 0.25) -> None:
        self.registry = registry
        self.store = store
        self.circuit_breaker = circuit_breaker
        self.rate_limiter = rate_limiter
        self.backoff_base_seconds = backoff_base_seconds
        self._idempotency_locks: dict[str, asyncio.Lock] = {}

    async def execute(self, request: RuntimeRequest) -> RuntimeExecution:
        if request.idempotency_key:
            lock = self._idempotency_locks.setdefault(request.idempotency_key, asyncio.Lock())
            async with lock:
                return await self._execute_locked(request)
        return await self._execute_locked(request)

    async def _execute_locked(self, request: RuntimeRequest) -> RuntimeExecution:
        if request.idempotency_key:
            old = await self.store.by_idempotency_key(request.idempotency_key)
            if old and old.status == ExecutionStatus.SUCCEEDED:
                return old

        key = f"{request.provider}:{request.workflow}"
        execution = RuntimeExecution(
            provider=request.provider, workflow=request.workflow,
            correlation_id=get_or_create_correlation_id(request.correlation_id),
            idempotency_key=request.idempotency_key,
        )

        if not self.rate_limiter.allow(key):
            execution.status = ExecutionStatus.REJECTED
            execution.error = "Rate limit exceeded"
            await self.store.save(execution)
            return execution

        if not self.circuit_breaker.allow(key):
            execution.status = ExecutionStatus.REJECTED
            execution.error = "Circuit breaker is open"
            await self.store.save(execution)
            return execution

        try:
            adapter = self.registry.get(request.provider)
        except KeyError as exc:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(exc)
            await self.store.save(execution)
            return execution

        execution.status = ExecutionStatus.RUNNING
        await self.store.save(execution)

        for attempt in range(1, request.max_retries + 2):
            execution.attempts = attempt
            try:
                result = await asyncio.wait_for(
                    adapter.execute(
                        IntegrationRequest(
                            workflow=request.workflow,
                            payload=request.payload,
                            correlation_id=execution.correlation_id,
                            timeout_seconds=request.timeout_seconds,
                        )
                    ),
                    timeout=request.timeout_seconds,
                )
            except TimeoutError:
                result = None
                execution.error = "Integration execution timed out"
            except asyncio.CancelledError:
                execution.status = ExecutionStatus.FAILED
                execution.error = "Integration execution cancelled"
                execution.updated_at = datetime.now(UTC)
                await self.store.save(execution)
                raise
            except Exception as exc:  # noqa: BLE001 - adapter failures become execution results
                result = None
                execution.error = f"Integration adapter failed: {type(exc).__name__}"

            if result is None:
                if attempt <= request.max_retries:
                    await asyncio.sleep(self.backoff_base_seconds * (2 ** (attempt - 1)))
                continue
            if result.success:
                execution.status = ExecutionStatus.SUCCEEDED
                execution.data = result.data
                execution.error = None
                execution.updated_at = datetime.now(UTC)
                self.circuit_breaker.success(key)
                await self.store.save(execution)
                return execution
            execution.error = result.error or "Integration failed"
            if attempt <= request.max_retries:
                await asyncio.sleep(self.backoff_base_seconds * (2 ** (attempt - 1)))

        execution.status = ExecutionStatus.FAILED
        execution.updated_at = datetime.now(UTC)
        self.circuit_breaker.failure(key)
        await self.store.save(execution)
        return execution
