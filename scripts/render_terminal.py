#!/usr/bin/env python3
"""Gera o terminal do perfil com a Eva em destaque e a atividade pública recente."""

import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USER = "Ilhe8l"
FEATURED = "eva"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "terminal.svg"

STATS_QUERY = """
query($login: String!, $repo: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
    repository(name: $repo) { stargazerCount }
  }
}
"""


def github(url: str, payload: dict | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ilhe8l-profile-renderer",
    }
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode() if payload else None
    with urlopen(Request(url, data=data, headers=headers), timeout=15) as response:
        return json.load(response)


def fetch_stats() -> dict:
    # A API GraphQL exige token; no workflow o GITHUB_TOKEN já basta.
    result = github(
        "https://api.github.com/graphql",
        {"query": STATS_QUERY, "variables": {"login": USER, "repo": FEATURED}},
    )
    if result.get("errors"):
        raise RuntimeError(result["errors"][0]["message"])
    user = result["data"]["user"]
    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    weeks = [sum(day["contributionCount"] for day in week["contributionDays"]) for week in calendar["weeks"]]
    return {
        "contributions": calendar["totalContributions"],
        "commits": collection["totalCommitContributions"],
        "pull_requests": collection["totalPullRequestContributions"],
        "repositories": collection["totalRepositoriesWithContributedCommits"],
        "weeks": weeks[-52:],
        "stars": user["repository"]["stargazerCount"],
    }


def latest_public_commit() -> tuple[str, str, datetime]:
    # A busca cobre qualquer repositório público, inclusive os da organização.
    query = urlencode({"q": f"author:{USER} is:public", "sort": "committer-date", "per_page": 1})
    items = github(f"https://api.github.com/search/commits?{query}")["items"]
    if not items:
        raise RuntimeError("Nenhum commit público encontrado")
    commit = items[0]
    message = commit["commit"]["message"].splitlines()[0]
    committed_at = datetime.fromisoformat(commit["commit"]["committer"]["date"])
    return commit["repository"]["full_name"], message, committed_at


def shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def sparkline(weeks: list[int], x: int, baseline: int, height: int) -> str:
    # Raiz quadrada para uma semana atípica não achatar o resto do gráfico.
    peak = max(weeks) ** 0.5 or 1
    bars = []
    for index, count in enumerate(weeks):
        bar = max(3, round(count**0.5 / peak * height))
        color = "#27384a" if not count else "#9ece6a" if count**0.5 >= peak / 2 else "#4f7a3a"
        bars.append(
            f'<rect x="{x + index * 17}" y="{baseline - bar}" width="13" height="{bar}" rx="1.5" fill="{color}"/>'
        )
    return "\n    ".join(bars)


def render(stats: dict, repository: str, message: str, committed_at: datetime) -> str:
    numbers = (
        f"{stats['contributions']:,} contributions · {stats['commits']:,} commits · "
        f"{stats['pull_requests']:,} PRs · {stats['repositories']} repos"
    )
    latest = f"{repository} · {committed_at:%d %b %Y}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 960 640" role="img" aria-labelledby="title desc">
  <title id="title">Guilherme Souza, AI and backend developer</title>
  <desc id="desc">Terminal-style profile featuring Eva, a local voice assistant, plus work on EDITE and Oráculo. Last year: {escape(numbers)}. Latest public commit: {escape(latest)}.</desc>
  <rect x="1" y="1" width="958" height="638" rx="16" fill="#0d1117" stroke="#303d4d" stroke-width="2"/>
  <path d="M17 1h926a16 16 0 0 1 16 16v34H1V17A16 16 0 0 1 17 1Z" fill="#161f2a"/>
  <path d="M1 51h958" stroke="#303d4d"/>
  <circle cx="28" cy="26" r="6" fill="#f7768e"/>
  <circle cx="49" cy="26" r="6" fill="#e0af68"/>
  <circle cx="70" cy="26" r="6" fill="#9ece6a"/>
  <g font-family="ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace" font-size="16">
    <text x="480" y="31" text-anchor="middle" font-size="14" fill="#95a6bb">guilherme@github: ~</text>

    <text x="36" y="88" fill="#7dcfff">$ whoami</text>
    <text x="36" y="126" font-size="29" font-weight="700" fill="#edf2f7">Guilherme Souza</text>
    <text x="36" y="155" fill="#b9c5d2">AI &amp; backend developer / Information Systems student at IFES</text>
    <path d="M36 176h888" stroke="#27384a"/>

    <text x="36" y="206" fill="#7dcfff">$ eva --about</text>
    <text x="36" y="240" font-size="22" font-weight="700" fill="#bb9af7">Eva</text>
    <text x="92" y="240" fill="#e0af68">★ {stats['stars']}</text>
    <text x="160" y="240" fill="#95a6bb">Python · MIT · github.com/{USER}/{FEATURED}</text>
    <text x="36" y="268" fill="#d4dde7">A personal voice assistant that lives on your computer.</text>
    <text x="36" y="293" fill="#95a6bb">Deep Agents + LangGraph · local speech · skills she writes herself</text>
    <path d="M36 314h888" stroke="#27384a"/>

    <text x="36" y="344" fill="#7dcfff">$ current_work --at LEDS</text>
    <text x="36" y="375" fill="#9ece6a">EDITE</text>
    <text x="139" y="375" fill="#d4dde7">AI assistant for FAPES</text>
    <text x="36" y="402" fill="#9ece6a">ORÁCULO</text>
    <text x="139" y="402" fill="#d4dde7">natural-language-to-SQL tool for FAPES</text>
    <path d="M36 423h888" stroke="#27384a"/>

    <text x="36" y="453" fill="#7dcfff">$ git stats --last-year</text>
    <text x="36" y="483" fill="#d4dde7">{escape(numbers)}</text>
    {sparkline(stats['weeks'], 36, 532, 36)}
    <path d="M36 551h888" stroke="#27384a"/>

    <text x="36" y="581" fill="#7dcfff">$ git log -1 --public</text>
    <text x="36" y="611" fill="#e0af68" xml:space="preserve">{escape(latest)}  <tspan fill="#d4dde7">{escape(shorten(message, 84 - len(latest)))}</tspan></text>
    <text x="914" y="611" text-anchor="end" fill="#9ece6a">▌</text>
  </g>
</svg>
"""


if __name__ == "__main__":
    card = render(fetch_stats(), *latest_public_commit())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(card, encoding="utf-8")
