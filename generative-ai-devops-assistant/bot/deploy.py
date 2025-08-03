# bot/deploy.py
import os
import aiohttp

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def trigger_github_workflow(repo: str, workflow_id: str, ref: str = "main"):
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"ref": ref}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            resp_text = await resp.text()
            return resp.status, resp_text
