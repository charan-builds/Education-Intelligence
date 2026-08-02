from __future__ import annotations

import re

import httpx


class GitHubProfileService:
    USERNAME_RE = re.compile(r"github\.com/([^/?#]+)")

    def __init__(self) -> None:
        self.base_headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "UniversalLearningIntelligencePlatform",
        }

    def extract_username(self, github_url: str) -> str | None:
        match = self.USERNAME_RE.search(github_url.strip())
        if not match:
            return None
        return match.group(1).strip() or None

    async def fetch_summary(self, github_url: str) -> dict[str, object]:
        username = self.extract_username(github_url)
        if not username:
            return {}

        async with httpx.AsyncClient(timeout=8.0, headers=self.base_headers) as client:
            repos_response = await client.get(f"https://api.github.com/users/{username}/repos", params={"per_page": 100, "sort": "updated"})
            repos_response.raise_for_status()
            repos = list(repos_response.json() or [])

        languages: dict[str, int] = {}
        active_repos = 0
        for repo in repos:
            language = str(repo.get("language") or "").strip()
            if language:
                languages[language] = languages.get(language, 0) + 1
            if not bool(repo.get("fork")):
                active_repos += 1

        repo_count = len(repos)
        activity_score = min(100.0, round((repo_count * 2.8) + (active_repos * 1.2), 2))
        return {
            "github_repo_count": repo_count,
            "github_languages": sorted(languages.keys())[:12],
            "github_activity_score": activity_score,
        }
