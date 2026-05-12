from __future__ import annotations

import re
from urllib.parse import quote, quote_plus

import httpx
from github import Github

from src.application import ValidationAppError
from src.domain.ports.services import IGitHubService

_GITHUB_ACCEPT = "application/vnd.github+json"
_GITHUB_API_VERSION = "2022-11-28"


def _github_rest_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": _GITHUB_ACCEPT,
        "X-GitHub-Api-Version": _GITHUB_API_VERSION,
    }


def _parse_last_page_from_link_header(link_header: str | None) -> int | None:
    if not link_header:
        return None
    for segment in link_header.split(","):
        if 'rel="last"' not in segment and "rel='last'" not in segment:
            continue
        m = re.search(r"[?&]page=(\d+)", segment)
        if m:
            return int(m.group(1))
    return None


def _user_repos_total_estimate(
    link_header: str | None, page: int, per_page: int, items_len: int
) -> int:
    last_page = _parse_last_page_from_link_header(link_header)
    if last_page is not None:
        return (last_page - 1) * per_page + per_page
    if items_len < per_page:
        return (page - 1) * per_page + items_len
    return page * per_page + 1


class PyGitHubService(IGitHubService):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        callback_url: str,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = callback_url

    def build_authorization_url(self, state: str) -> str:
        return (
            "https://github.com/login/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.callback_url}"
            "&scope=repo,read:org"
            f"&state={state}"
        )

    async def exchange_code_for_token(self, code: str) -> tuple[str, str]:
        url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload, headers=headers)

        data = response.json()
        token = data.get("access_token")
        token_type = data.get("token_type", "bearer")

        if not token:
            raise ValidationAppError("Could not retrieve GitHub access token")

        return token, token_type

    async def list_repositories(self, access_token: str) -> list[str]:
        gh = Github(access_token)
        user = gh.get_user()
        return [repo.full_name for repo in user.get_repos()]

    async def list_branches(self, repository: str, access_token: str) -> list[str]:
        gh = Github(access_token)
        repo = gh.get_repo(repository)
        return [branch.name for branch in repo.get_branches()]

    async def list_tags(self, repository: str, access_token: str) -> list[str]:
        gh = Github(access_token)
        repo = gh.get_repo(repository)
        return [tag.name for tag in repo.get_tags()]

    async def ref_exists(
        self, repository: str, ref_name: str, access_token: str
    ) -> bool:
        branches = await self.list_branches(repository, access_token)
        tags = await self.list_tags(repository, access_token)
        return ref_name in branches or ref_name in tags

    async def _list_user_repos_page(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        page: int,
        per_page: int,
    ) -> tuple[list[str], int]:
        r = await client.get(
            "https://api.github.com/user/repos",
            params={
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "affiliation": "owner,collaborator,organization_member",
            },
            headers=headers,
        )
        if r.status_code != 200:
            data = r.json()
            msg = data.get("message", r.text) if isinstance(data, dict) else r.text
            raise ValidationAppError(f"Não foi possível listar repositórios: {msg}")
        rows = r.json()
        if not isinstance(rows, list):
            raise ValidationAppError("Resposta inválida da API GitHub (user/repos).")
        items = [row["full_name"] for row in rows if isinstance(row, dict) and "full_name" in row]
        total = _user_repos_total_estimate(r.headers.get("Link"), page, per_page, len(items))
        return items, total

    async def _filter_user_repos_by_substring(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        needle: str,
        page: int,
        per_page: int,
    ) -> tuple[list[str], int]:
        n = needle.strip().lower()
        names: list[str] = []
        max_pages = 10
        for p in range(1, max_pages + 1):
            r = await client.get(
                "https://api.github.com/user/repos",
                params={
                    "page": p,
                    "per_page": 100,
                    "sort": "updated",
                    "affiliation": "owner,collaborator,organization_member",
                },
                headers=headers,
            )
            if r.status_code != 200:
                break
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            for row in batch:
                if not isinstance(row, dict):
                    continue
                fn = row.get("full_name", "")
                if isinstance(fn, str) and n in fn.lower():
                    names.append(fn)
            if len(batch) < 100:
                break
        total = len(names)
        offset = (page - 1) * per_page
        return names[offset : offset + per_page], total

    async def search_repositories(
        self, access_token: str, query: str, page: int, per_page: int
    ) -> tuple[list[str], int]:
        per_req = min(max(per_page, 1), 100)
        page_req = max(page, 1)
        headers = _github_rest_headers(access_token)
        async with httpx.AsyncClient(timeout=25.0) as client:
            r_user = await client.get("https://api.github.com/user", headers=headers)
            if r_user.status_code != 200:
                raise ValidationAppError("Token GitHub inválido ou sem permissão.")
            login = r_user.json().get("login")
            if not login:
                raise ValidationAppError("Não foi possível obter o utilizador GitHub.")

            q = query.strip()
            if not q:
                return await self._list_user_repos_page(
                    client, headers, page_req, per_req
                )

            fragment = quote_plus(q)
            search_q = f"user:{login}+fork:true+in:name+{fragment}"
            r = await client.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": search_q,
                    "page": page_req,
                    "per_page": per_req,
                },
                headers=headers,
            )
            data = r.json()
            if r.status_code == 200 and isinstance(data, dict):
                items = [
                    it["full_name"]
                    for it in data.get("items", [])
                    if isinstance(it, dict) and "full_name" in it
                ]
                total = int(data.get("total_count", 0))
                return items, total

            if r.status_code in (403, 422):
                return await self._filter_user_repos_by_substring(
                    client, headers, q, page_req, per_req
                )

            msg = data.get("message", r.text) if isinstance(data, dict) else r.text
            raise ValidationAppError(f"Falha na pesquisa GitHub: {msg}")

    async def search_refs(
        self, access_token: str, repository: str, query: str, limit: int
    ) -> tuple[list[str], list[str]]:
        repo_key = repository.strip()
        if "/" not in repo_key:
            raise ValidationAppError("Repositório deve estar no formato owner/repo.")

        owner, _, name = repo_key.partition("/")
        if not name or "/" in name:
            raise ValidationAppError("Repositório deve estar no formato owner/repo.")

        lim = min(max(limit, 1), 100)
        headers = _github_rest_headers(access_token)
        base = f"https://api.github.com/repos/{owner}/{name}"

        async with httpx.AsyncClient(timeout=25.0) as client:
            if not query.strip():
                r = await client.get(base, headers=headers)
                if r.status_code != 200:
                    data = r.json()
                    msg = (
                        data.get("message", r.text)
                        if isinstance(data, dict)
                        else r.text
                    )
                    raise ValidationAppError(
                        f"Repositório inacessível ou inexistente: {msg}"
                    )
                default_branch = r.json().get("default_branch") or "main"
                return [default_branch], []

            pref = quote(query.strip(), safe="")
            branches: list[str] = []
            tags: list[str] = []

            rb = await client.get(
                f"{base}/git/matching-refs/heads/{pref}",
                headers=headers,
            )
            if rb.status_code == 200:
                for item in rb.json():
                    ref = item.get("ref", "")
                    if ref.startswith("refs/heads/"):
                        branches.append(ref.removeprefix("refs/heads/"))
            elif rb.status_code not in (404, 422):
                rb.raise_for_status()

            rt = await client.get(
                f"{base}/git/matching-refs/tags/{pref}",
                headers=headers,
            )
            if rt.status_code == 200:
                for item in rt.json():
                    ref = item.get("ref", "")
                    if ref.startswith("refs/tags/"):
                        tags.append(ref.removeprefix("refs/tags/"))
            elif rt.status_code not in (404, 422):
                rt.raise_for_status()

            out_b: list[str] = []
            out_t: list[str] = []
            for b in branches:
                if len(out_b) + len(out_t) >= lim:
                    break
                out_b.append(b)
            for t in tags:
                if len(out_b) + len(out_t) >= lim:
                    break
                out_t.append(t)
            return out_b, out_t
