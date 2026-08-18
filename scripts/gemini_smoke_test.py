import asyncio
import os

from app.llm.base import LLMRequest
from app.llm.factory import build_llm_provider


async def main() -> None:
    if os.getenv("AGENT_OS_LLM_PROVIDER") != "gemini":
        raise SystemExit(
            "Set AGENT_OS_LLM_PROVIDER=gemini before running this smoke test."
        )

    provider = build_llm_provider()
    result = await provider.generate(
        LLMRequest(
            system="You are a concise test agent.",
            prompt="Reply with exactly: AGENT_OS_GEMINI_OK",
        )
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
