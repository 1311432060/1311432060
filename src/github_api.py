import sys
import time

import requests

import config


class GitHubClient:
    def __init__(self, username: str = config.USERNAME, token: str = config.TOKEN):
        self.username = username
        self.token = token
        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-custom-badge",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)

    def _get(self, path: str, **params) -> dict:
        url = path if path.startswith("http") else f"{config.GITHUB_API}{path}"
        for attempt in range(3):
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            if response.status_code in (403, 429) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            response.raise_for_status()
        raise RuntimeError(f"GitHub API request failed: {url}")

    def _graphql(self, query: str, **variables) -> dict:
        if not self.token:
            return {}
        response = self.session.post(
            config.GITHUB_GRAPHQL_API,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        if response.status_code != 200:
            print(f"[warn] GraphQL request failed: {response.status_code}", file=sys.stderr)
            return {}
        payload = response.json()
        if "errors" in payload:
            print(f"[warn] GraphQL errors: {payload['errors']}", file=sys.stderr)
            return {}
        return payload.get("data") or {}

    def user(self) -> dict:
        return self._get(f"/users/{self.username}")

    def repositories(self) -> list:
        repos, page = [], 1
        while True:
            chunk = self._get(
                f"/users/{self.username}/repos",
                per_page=100,
                page=page,
                sort="updated",
            )
            if not chunk:
                break
            repos.extend(chunk)
            if len(chunk) < 100:
                break
            page += 1
        return repos

    def repo_languages(self, repo_full_name: str) -> dict:
        return self._get(f"/repos/{repo_full_name}/languages")

    def contributions(self) -> int:
        query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar { totalContributions }
            }
          }
        }
        """
        data = self._graphql(query, login=self.username)
        try:
            return data["user"]["contributionsCollection"]["contributionCalendar"][
                "totalContributions"
            ]
        except (KeyError, TypeError):
            return 0


def collect_stats(client: GitHubClient) -> dict:
    user = client.user()
    repos = client.repositories()

    counted = [
        repo
        for repo in repos
        if (config.INCLUDE_FORKS or not repo.get("fork"))
        and repo["name"] not in config.EXCLUDE_REPOS
        and not repo.get("archived")
    ]

    stars = sum(repo.get("stargazers_count", 0) for repo in counted)
    forks = sum(repo.get("forks_count", 0) for repo in counted)

    languages: dict = {}
    for repo in counted:
        if repo.get("size", 0) == 0:
            continue
        for name, size in client.repo_languages(repo["full_name"]).items():
            if name.lower() in config.EXCLUDE_LANGS:
                continue
            languages[name] = languages.get(name, 0) + size

    languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=True))

    return {
        "username": user.get("login", client.username),
        "name": user.get("name") or user.get("login", client.username),
        "avatar_url": user.get("avatar_url", ""),
        "bio": user.get("bio") or "",
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "public_repos": user.get("public_repos", 0),
        "owned_repos": len(counted),
        "stars": stars,
        "forks": forks,
        "contributions": client.contributions(),
        "languages": languages,
    }
