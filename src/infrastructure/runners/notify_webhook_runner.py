import httpx
from src.domain.entities.pipeline_step import PipelineStep


class NotifyWebhookRunner:
    async def run(self, step: PipelineStep) -> tuple[int, str]:
        webhook_url = step.command.strip()
        payload = {"message": "pipeline notification step"}
        async with httpx.AsyncClient(timeout=step.timeout_seconds) as client:
            response = await client.post(webhook_url, json=payload)
            if 200 <= response.status_code < 300:
                return 0, f"webhook ok: {response.status_code}"
            return 1, f"webhook failed: {response.status_code}"