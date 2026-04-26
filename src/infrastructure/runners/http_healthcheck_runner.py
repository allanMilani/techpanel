import httpx
from src.domain.entities.pipeline_step import PipelineStep

class HttpHealthcheckRunner:
    async def run(self, step: PipelineStep) -> tuple[int, str]:
        url = step.command.strip()
        async with httpx.AsyncClient(timeout=step.timeout_seconds) as client:
            response = await client.get(url)
            if 200 <= response.status_code < 300:
                return 0, f"Healthcheck ok: {response.status_code}"
            return 1, f"Healthcheck failed: {response.status_code}"